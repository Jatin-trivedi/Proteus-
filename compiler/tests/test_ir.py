"""
Unit Tests for JOCKY AST -> IR Generator (Priority 3.3)
"""
import unittest
import json
from compiler.compiler import Compiler
from compiler.parser.ast import Program, AnalysisBlock, FunctionCall, Argument
from compiler.ir.generator import IRGenerator
from compiler.ir.model import IRValidationError, IRDocument, IROperation


class TestIRGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = IRGenerator()
        self.compiler = Compiler()

    def test_single_operation(self):
        source = '''
        analysis "Single Op Investigation" {
            system.info();
        }
        '''
        result = self.compiler.compile(source)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.ir)

        expected = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Single Op Investigation",
            "operations": [
                {
                    "id": "op-001",
                    "type": "system.info",
                    "parameters": {},
                }
            ],
        }
        self.assertEqual(result.ir, expected)

    def test_multiple_operations(self):
        source = '''
        analysis "Network Investigation" {
            system.info();
            network.connections();
            network.dns();
        }
        '''
        result = self.compiler.compile(source)
        self.assertTrue(result.success)

        expected = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Network Investigation",
            "operations": [
                {
                    "id": "op-001",
                    "type": "system.info",
                    "parameters": {},
                },
                {
                    "id": "op-002",
                    "type": "network.connections",
                    "parameters": {},
                },
                {
                    "id": "op-003",
                    "type": "network.dns",
                    "parameters": {},
                },
            ],
        }
        self.assertEqual(result.ir, expected)

    def test_parameterized_operations(self):
        source = '''
        analysis "Parameterized Ops" {
            processes.details(1234);
            filesystem.hash("./evidence/malware.bin");
            filesystem.metadata("/etc/shadow");
        }
        '''
        result = self.compiler.compile(source)
        self.assertTrue(result.success)

        ops = result.ir["operations"]
        self.assertEqual(len(ops), 3)

        # processes.details(1234) -> parameter 'pid'
        self.assertEqual(ops[0]["id"], "op-001")
        self.assertEqual(ops[0]["type"], "processes.details")
        self.assertEqual(ops[0]["parameters"], {"pid": 1234})

        # filesystem.hash("./evidence/malware.bin") -> parameter 'path'
        self.assertEqual(ops[1]["id"], "op-002")
        self.assertEqual(ops[1]["type"], "filesystem.hash")
        self.assertEqual(ops[1]["parameters"], {"path": "./evidence/malware.bin"})

        # filesystem.metadata("/etc/shadow") -> parameter 'path'
        self.assertEqual(ops[2]["id"], "op-003")
        self.assertEqual(ops[2]["type"], "filesystem.metadata")
        self.assertEqual(ops[2]["parameters"], {"path": "/etc/shadow"})

    def test_operation_ordering_and_sequential_ids(self):
        source = '''
        analysis "Ordered Ops" {
            system.info();
            system.users();
            processes.list();
            processes.details(500);
            network.interfaces();
            network.connections();
        }
        '''
        result = self.compiler.compile(source)
        self.assertTrue(result.success)

        ops = result.ir["operations"]
        expected_ids = ["op-001", "op-002", "op-003", "op-004", "op-005", "op-006"]
        expected_types = [
            "system.info",
            "system.users",
            "processes.list",
            "processes.details",
            "network.interfaces",
            "network.connections",
        ]

        self.assertEqual([op["id"] for op in ops], expected_ids)
        self.assertEqual([op["type"] for op in ops], expected_types)

    def test_complete_investigation_ast_to_ir(self):
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
        result = self.compiler.compile(source)
        self.assertTrue(result.success)
        self.assertEqual(result.ir["investigation"], "Complete System Investigation")
        self.assertEqual(len(result.ir["operations"]), 9)

        # Validate deserialization into IRDocument model
        doc = IRDocument.from_dict(result.ir)
        self.assertEqual(len(doc.operations), 9)
        self.assertEqual(doc.operations[0].id, "op-001")
        self.assertEqual(doc.operations[8].id, "op-009")
        self.assertEqual(doc.operations[8].parameters, {"path": "./evidence"})

    def test_invalid_ast_and_unknown_function_boundary(self):
        # Non-Program input to generator
        with self.assertRaises(IRValidationError):
            self.generator.generate("not a program")

        # Function not registered in registry
        fake_call = FunctionCall(namespace="unknown", function="fake", arguments=[])
        bad_block = AnalysisBlock(name="Bad Block", statements=[fake_call])
        bad_prog = Program(body=[bad_block])

        with self.assertRaises(IRValidationError):
            self.generator.generate(bad_prog)

    def test_deterministic_ir_serialization(self):
        source = '''
        analysis "Deterministic Test" {
            system.info();
            network.routes();
            filesystem.hash("/tmp/file");
        }
        '''
        res1 = self.compiler.compile(source)
        res2 = self.compiler.compile(source)

        self.assertEqual(
            json.dumps(res1.ir, sort_keys=True),
            json.dumps(res2.ir, sort_keys=True),
        )


if __name__ == "__main__":
    unittest.main()
