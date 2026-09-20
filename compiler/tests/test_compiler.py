"""
End-to-End Compiler Pipeline Tests for Priority 3.3
"""
import unittest
from compiler import compile, check
from compiler.diagnostics import DiagnosticCode


class TestCompiler(unittest.TestCase):
    def test_compiler_complete_investigation(self):
        source = '''
        analysis "Complete System Investigation" {
            system.info();
            system.users();
            processes.list();
            network.interfaces();
            network.connections();
            network.routes();
            network.dns();
            filesystem.metadata("./evidence");
            filesystem.hash("./evidence");
        }
        '''
        result = compile(source, filename="complete_investigation.jocky")
        self.assertTrue(result.success)
        self.assertEqual(len(result.diagnostics), 0)
        self.assertIsNotNone(result.ast)
        self.assertIsNotNone(result.ir)
        self.assertEqual(result.ir["investigation"], "Complete System Investigation")
        self.assertEqual(result.ir["ir_type"], "jocky_forensic_ir")
        self.assertEqual(len(result.ir["operations"]), 9)

        # Check sequential IDs op-001..op-009
        expected_ids = [f"op-{i:03d}" for i in range(1, 10)]
        actual_ids = [op["id"] for op in result.ir["operations"]]
        self.assertEqual(actual_ids, expected_ids)

        # Check operation types
        expected_types = [
            "system.info",
            "system.users",
            "processes.list",
            "network.interfaces",
            "network.connections",
            "network.routes",
            "network.dns",
            "filesystem.metadata",
            "filesystem.hash",
        ]
        actual_types = [op["type"] for op in result.ir["operations"]]
        self.assertEqual(actual_types, expected_types)

        # Check parameters
        self.assertEqual(result.ir["operations"][0]["parameters"], {})
        self.assertEqual(result.ir["operations"][7]["parameters"], {"path": "./evidence"})
        self.assertEqual(result.ir["operations"][8]["parameters"], {"path": "./evidence"})

    def test_compiler_pipeline_invalid_script(self):
        source = '''
        analysis "Invalid Investigation" {
            system.fakeFunction();
            network.connections(123);
            processes.details();
        }
        '''
        result = compile(source, filename="invalid.jocky")
        self.assertFalse(result.success)
        self.assertGreater(len(result.diagnostics), 0)
        self.assertIsNone(result.ir)

        diag_text = result.format_diagnostics()
        self.assertIn("JOCKY-E2002", diag_text)
        self.assertIn("Unknown forensic function 'system.fakeFunction'", diag_text)

    def test_compiler_check_mode(self):
        valid_source = '''
        analysis "Check Only" {
            system.info();
            processes.list();
        }
        '''
        res = check(valid_source)
        self.assertTrue(res.success)
        self.assertIsNone(res.ir)  # check mode does not generate IR
        self.assertIsNotNone(res.ast)

        invalid_source = '''
        analysis "Check Fail" {
            storage.fake();
        }
        '''
        res_fail = check(invalid_source)
        self.assertFalse(res_fail.success)
        self.assertGreater(len(res_fail.diagnostics), 0)


if __name__ == "__main__":
    unittest.main()
