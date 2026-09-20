"""
Unit Tests for JOCKY IR Data Models (Priority 3.2)
"""
import unittest
import json
from compiler.ir.model import IRDocument, IROperation, IRValidationError


class TestIRModels(unittest.TestCase):
    def test_iroperation_construction_and_to_dict(self):
        op = IROperation(
            id="op-001",
            type="network.connections",
            parameters={},
        )
        self.assertEqual(op.id, "op-001")
        self.assertEqual(op.type, "network.connections")
        self.assertEqual(op.parameters, {})

        d = op.to_dict()
        expected = {
            "id": "op-001",
            "type": "network.connections",
            "parameters": {},
        }
        self.assertEqual(d, expected)

    def test_iroperation_parameterized(self):
        op1 = IROperation(
            id="op-001",
            type="processes.details",
            parameters={"pid": 1234},
        )
        self.assertEqual(op1.parameters, {"pid": 1234})
        self.assertEqual(op1.to_dict()["parameters"], {"pid": 1234})

        op2 = IROperation(
            id="op-002",
            type="filesystem.hash",
            parameters={"path": "./evidence"},
        )
        self.assertEqual(op2.parameters, {"path": "./evidence"})
        self.assertEqual(op2.to_dict()["parameters"], {"path": "./evidence"})

    def test_iroperation_serialization_deserialization(self):
        op = IROperation(
            id="op-042",
            type="filesystem.metadata",
            parameters={"path": "/var/log/syslog"},
        )
        json_str = op.to_json()
        self.assertIn('"id": "op-042"', json_str)
        self.assertIn('"type": "filesystem.metadata"', json_str)
        self.assertIn('"path": "/var/log/syslog"', json_str)

        reconstructed = IROperation.from_json(json_str)
        self.assertEqual(reconstructed.id, "op-042")
        self.assertEqual(reconstructed.type, "filesystem.metadata")
        self.assertEqual(reconstructed.parameters, {"path": "/var/log/syslog"})

    def test_irdocument_construction_and_serialization(self):
        op1 = IROperation(id="op-001", type="system.info", parameters={})
        op2 = IROperation(id="op-002", type="network.connections", parameters={})
        op3 = IROperation(id="op-003", type="network.dns", parameters={})

        doc = IRDocument(
            investigation="Network Investigation",
            operations=[op1, op2, op3],
        )

        self.assertEqual(doc.version, "1.0")
        self.assertEqual(doc.ir_type, "jocky_forensic_ir")
        self.assertEqual(doc.investigation, "Network Investigation")
        self.assertEqual(len(doc.operations), 3)

        expected_dict = {
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

        self.assertEqual(doc.to_dict(), expected_dict)

    def test_irdocument_deserialization_from_dict_and_json(self):
        raw_dict = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Complete Triage",
            "operations": [
                {
                    "id": "op-001",
                    "type": "processes.details",
                    "parameters": {"pid": 500},
                },
                {
                    "id": "op-002",
                    "type": "filesystem.hash",
                    "parameters": {"path": "/tmp/suspicious"},
                },
            ],
        }

        doc = IRDocument.from_dict(raw_dict)
        self.assertEqual(doc.investigation, "Complete Triage")
        self.assertEqual(len(doc.operations), 2)
        self.assertIsInstance(doc.operations[0], IROperation)
        self.assertEqual(doc.operations[0].id, "op-001")
        self.assertEqual(doc.operations[0].parameters["pid"], 500)

        # JSON round-trip
        json_str = doc.to_json()
        doc_from_json = IRDocument.from_json(json_str)
        self.assertEqual(doc_from_json.to_dict(), raw_dict)

    def test_irdocument_preserves_order_and_determinism(self):
        ops = [
            IROperation(id=f"op-{i:03d}", type=f"ns.func_{i}", parameters={"step": i})
            for i in range(1, 10)
        ]
        doc1 = IRDocument(investigation="Deterministic Test", operations=ops)
        doc2 = IRDocument(investigation="Deterministic Test", operations=ops)

        self.assertEqual(doc1.to_json(), doc2.to_json())
        self.assertEqual(
            [op.id for op in doc1.operations],
            [f"op-{i:03d}" for i in range(1, 10)],
        )

    def test_malformed_data_rejection(self):
        # Invalid operation ID (empty or non-string)
        with self.assertRaises(IRValidationError):
            IROperation(id="", type="system.info")
        with self.assertRaises(IRValidationError):
            IROperation(id=123, type="system.info")

        # Invalid operation type
        with self.assertRaises(IRValidationError):
            IROperation(id="op-001", type="")

        # Invalid operation parameters (non-dict)
        with self.assertRaises(IRValidationError):
            IROperation(id="op-001", type="system.info", parameters=["not", "a", "dict"])

        # Invalid document investigation
        with self.assertRaises(IRValidationError):
            IRDocument(investigation="", operations=[])

        # Missing required fields in from_dict
        with self.assertRaises(IRValidationError):
            IRDocument.from_dict({"version": "1.0", "operations": []})


if __name__ == "__main__":
    unittest.main()
