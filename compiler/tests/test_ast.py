"""
Unit Tests for JOCKY AST
"""
import unittest
import json
from compiler.parser.ast import Program, AnalysisBlock, FunctionCall, Argument


class TestAST(unittest.TestCase):
    def test_ast_node_creation(self):
        arg = Argument(value="./evidence", arg_type="string", line=4, column=21)
        self.assertEqual(arg.value, "./evidence")
        self.assertEqual(arg.arg_type, "string")
        self.assertEqual(arg.line, 4)
        self.assertEqual(arg.column, 21)

        call = FunctionCall(namespace="filesystem", function="hash", arguments=[arg], line=4, column=5)
        self.assertEqual(call.namespace, "filesystem")
        self.assertEqual(call.function, "hash")
        self.assertEqual(len(call.arguments), 1)

        block = AnalysisBlock(name="Network Investigation", statements=[call], line=1, column=1)
        self.assertEqual(block.name, "Network Investigation")
        self.assertEqual(len(block.statements), 1)

        prog = Program(body=[block])
        self.assertEqual(len(prog.analyses), 1)

    def test_ast_serialization_to_dict_and_json(self):
        call1 = FunctionCall(namespace="network", function="interfaces", arguments=[])
        call2 = FunctionCall(namespace="network", function="connections", arguments=[])
        call3 = FunctionCall(namespace="network", function="dns", arguments=[])
        block = AnalysisBlock(name="Network Investigation", statements=[call1, call2, call3])
        prog = Program(body=[block])

        d = prog.to_dict()
        expected = {
            "type": "Program",
            "analyses": [
                {
                    "type": "AnalysisBlock",
                    "name": "Network Investigation",
                    "statements": [
                        {
                            "type": "FunctionCall",
                            "namespace": "network",
                            "function": "interfaces",
                            "arguments": [],
                        },
                        {
                            "type": "FunctionCall",
                            "namespace": "network",
                            "function": "connections",
                            "arguments": [],
                        },
                        {
                            "type": "FunctionCall",
                            "namespace": "network",
                            "function": "dns",
                            "arguments": [],
                        },
                    ],
                }
            ],
        }
        self.assertEqual(d, expected)

        # JSON round-trip
        json_str = prog.to_json()
        self.assertIn('"type": "Program"', json_str)
        self.assertIn('"name": "Network Investigation"', json_str)
        parsed = json.loads(json_str)
        self.assertEqual(parsed, expected)


if __name__ == "__main__":
    unittest.main()
