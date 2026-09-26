"""
End-to-End Integration Tests for JOCKY Pipeline to Forensic Runtime (Priority 4.6)
JOCKY Source -> AST -> Semantic Validation -> IR -> IR Validation -> Dispatcher -> Collectors -> Result
"""

import os
import shutil
import tempfile
import unittest
import importlib.util

from compiler.compiler import Compiler
from compiler.ir.validator import IRValidator
from runtime.dispatcher import OperationDispatcher
from runtime.registry import create_default_registry, APPROVED_OPERATIONS
from runtime.errors import ErrorCode


def _load_local_agent_module():
    module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'local_agent.py'))
    spec = importlib.util.spec_from_file_location('local_agent_under_test', module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestE2ERuntime(unittest.TestCase):

    def setUp(self):
        self.compiler = Compiler()
        self.dispatcher = OperationDispatcher(create_default_registry())
        self.validator = IRValidator()

        # Set up temporary evidence directory and file
        self.evidence_dir = "evidence"
        os.makedirs(self.evidence_dir, exist_ok=True)
        self.sample_txt = os.path.join(self.evidence_dir, "sample.txt")
        with open(self.sample_txt, "w") as f:
            f.write("Forensic Baseline Evidence Sample Content\n")

    def tearDown(self):
        if os.path.exists(self.evidence_dir):
            shutil.rmtree(self.evidence_dir)

    def test_complete_forensic_baseline_e2e(self):
        """Verify full compilation and runtime execution of examples/forensic_baseline.jocky."""
        with open("examples/forensic_baseline.jocky") as f:
            source = f.read()

        # 1. Compile
        comp_res = self.compiler.compile(source, filename="examples/forensic_baseline.jocky")
        self.assertTrue(comp_res.success, f"Compilation failed: {comp_res.diagnostics}")
        self.assertIsNotNone(comp_res.ir)

        # 2. IR Validation
        self.assertTrue(self.validator.validate(comp_res.ir))
        self.assertEqual(len(comp_res.ir["operations"]), 9)

        # 3. Dispatch and Execute
        exec_res = self.dispatcher.dispatch(comp_res.ir)
        self.assertEqual(exec_res.investigation, "Forensic Baseline")
        self.assertEqual(exec_res.version, "1.0")
        self.assertEqual(len(exec_res.results), 9)

        # 4. Verify all 9 operations executed and succeeded
        for i, res in enumerate(exec_res.results):
            self.assertEqual(res.operation_id, f"op-{i+1:03d}")
            self.assertEqual(res.status, "success", f"Operation {res.type} failed: {res.error}")
            self.assertIsNotNone(res.data)
            self.assertIsNone(res.error)
            self.assertIsNotNone(res.duration_ms)
            self.assertGreaterEqual(res.duration_ms, 0)

        # 5. Check specific operation return schemas
        res_map = {r.type: r.data for r in exec_res.results}
        self.assertIn("hostname", res_map["system.info"])
        self.assertIn("users", res_map["system.users"])
        self.assertIn("processes", res_map["processes.list"])
        self.assertIn("interfaces", res_map["network.interfaces"])
        self.assertIn("connections", res_map["network.connections"])
        self.assertIn("routes", res_map["network.routes"])
        self.assertIn("dns_servers", res_map["network.dns"])
        self.assertIn("size", res_map["filesystem.metadata"])
        self.assertIn("hash", res_map["filesystem.hash"])
        self.assertEqual(res_map["filesystem.hash"]["algorithm"], "SHA-256")

    def test_all_10_approved_operations_pipeline(self):
        """Verify pipeline execution with all 10 approved operations including processes.details."""
        curr_pid = os.getpid()
        source = f'''
        analysis "Full Spectrum Investigation" {{
            system.info();
            system.users();
            processes.list();
            processes.details({curr_pid});
            network.interfaces();
            network.connections();
            network.routes();
            network.dns();
            filesystem.metadata("./evidence");
            filesystem.hash("./evidence/sample.txt");
        }}
        '''
        comp_res = self.compiler.compile(source, filename="<test>")
        self.assertTrue(comp_res.success)
        self.assertEqual(len(comp_res.ir["operations"]), 10)

        exec_res = self.dispatcher.dispatch(comp_res.ir)
        self.assertEqual(len(exec_res.results), 10)
        for r in exec_res.results:
            self.assertEqual(r.status, "success", f"Op {r.type} failed: {r.error}")

    def test_failure_isolation_in_pipeline(self):
        """Verify that when one operation fails, prior and subsequent operations still succeed."""
        source = '''
        analysis "Fault Isolation Test" {
            system.info();
            filesystem.hash("./non_existent_file_999.xyz");
            system.users();
        }
        '''
        comp_res = self.compiler.compile(source, filename="<test>")
        self.assertTrue(comp_res.success)


        exec_res = self.dispatcher.dispatch(comp_res.ir)
        self.assertEqual(len(exec_res.results), 3)

        self.assertEqual(exec_res.results[0].status, "success")
        self.assertEqual(exec_res.results[0].type, "system.info")

        self.assertEqual(exec_res.results[1].status, "error")
        self.assertEqual(exec_res.results[1].type, "filesystem.hash")
        self.assertEqual(exec_res.results[1].error.code, ErrorCode.COLLECTION_FAILED)

        self.assertEqual(exec_res.results[2].status, "success")
        self.assertEqual(exec_res.results[2].type, "system.users")

    def test_security_boundary_rejects_unapproved_operation(self):
        """Verify runtime security boundary rejects unapproved/evil operation without executing arbitrary commands."""
        malicious_ir = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Malicious Injection Attempt",
            "operations": [
                {
                    "id": "op-001",
                    "type": "evil.operation",
                    "parameters": {"cmd": "rm -rf /"}
                }
            ]
        }

        exec_res = self.dispatcher.dispatch(malicious_ir)
        self.assertEqual(len(exec_res.results), 1)
        self.assertEqual(exec_res.results[0].status, "error")
        self.assertEqual(exec_res.results[0].error.code, ErrorCode.UNKNOWN_OPERATION)
        self.assertIn("not recognized or permitted", exec_res.results[0].error.message)

    def test_local_agent_executes_ir_document_payloads(self):
        """IR JSON deployed by the manager must be treated as structured forensic work, not shell text."""
        local_agent = _load_local_agent_module()
        ir_document = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Local Agent IR Test",
            "operations": [{
                "id": "op-001",
                "type": "system.info",
                "parameters": {}
            }],
        }

        result = local_agent.execute_jocky_payload(__import__('json').dumps(ir_document))

        self.assertEqual(result["type"], "ir_document")
        self.assertIn("result", result)
        self.assertEqual(result["result"]["investigation"], "Local Agent IR Test")
        self.assertEqual(result["result"]["results"][0]["status"], "success")


if __name__ == "__main__":
    unittest.main()
