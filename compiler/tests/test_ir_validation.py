"""
Unit Tests for JOCKY IR Validation and JSON Serialization (Priority 3.4)
"""
import unittest
import json
import tempfile
import os
from compiler.ir.model import IRDocument, IROperation, IRValidationError
from compiler.ir.validator import IRValidator, validate_ir
from compiler.semantic.registry import DEFAULT_REGISTRY


class TestIRValidationAndSerialization(unittest.TestCase):
    def setUp(self):
        self.validator = IRValidator(DEFAULT_REGISTRY)

    def test_valid_ir(self):
        valid_dict = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Network Investigation",
            "operations": [
                {
                    "id": "op-001",
                    "type": "network.interfaces",
                    "parameters": {},
                },
                {
                    "id": "op-002",
                    "type": "network.connections",
                    "parameters": {},
                },
            ],
        }
        res = self.validator.validate(valid_dict)
        self.assertTrue(res.is_valid)
        self.assertEqual(len(res.errors), 0)
        self.assertIsNotNone(res.document)
        self.assertEqual(res.document.investigation, "Network Investigation")
        self.assertEqual(len(res.document.operations), 2)

    def test_missing_version(self):
        bad_dict = {
            "ir_type": "jocky_forensic_ir",
            "investigation": "Triage",
            "operations": [],
        }
        res = self.validator.validate(bad_dict)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("version" in err for err in res.errors))

    def test_invalid_version(self):
        bad_dict = {
            "version": "99.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Triage",
            "operations": [],
        }
        res = self.validator.validate(bad_dict)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Unsupported IR version '99.0'" in err for err in res.errors))

    def test_missing_investigation(self):
        bad_dict = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "operations": [],
        }
        res = self.validator.validate(bad_dict)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("investigation" in err for err in res.errors))

    def test_missing_operations(self):
        bad_dict = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Triage",
        }
        res = self.validator.validate(bad_dict)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("operations" in err for err in res.errors))

    def test_duplicate_operation_id(self):
        bad_dict = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Duplicate ID Test",
            "operations": [
                {
                    "id": "op-001",
                    "type": "system.info",
                    "parameters": {},
                },
                {
                    "id": "op-001",  # Duplicate ID
                    "type": "network.connections",
                    "parameters": {},
                },
            ],
        }
        res = self.validator.validate(bad_dict)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Duplicate operation ID 'op-001'" in err for err in res.errors))

    def test_missing_operation_type(self):
        bad_dict = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Missing Type Test",
            "operations": [
                {
                    "id": "op-001",
                    "parameters": {},
                }
            ],
        }
        res = self.validator.validate(bad_dict)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Missing required field 'type'" in err for err in res.errors))

    def test_unknown_operation_type(self):
        bad_dict = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Unknown Type Test",
            "operations": [
                {
                    "id": "op-001",
                    "type": "network.fakeFunction",
                    "parameters": {},
                }
            ],
        }
        res = self.validator.validate(bad_dict)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Unknown forensic function 'fakeFunction'" in err for err in res.errors))

    def test_invalid_parameters_missing_required(self):
        # processes.details requires 'pid'
        bad_dict = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Missing Param Test",
            "operations": [
                {
                    "id": "op-001",
                    "type": "processes.details",
                    "parameters": {},  # Missing 'pid'
                }
            ],
        }
        res = self.validator.validate(bad_dict)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Missing required parameter 'pid'" in err for err in res.errors))

    def test_invalid_parameters_wrong_type(self):
        # processes.details requires 'pid' as number, but got string
        bad_dict = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Wrong Param Type Test",
            "operations": [
                {
                    "id": "op-001",
                    "type": "processes.details",
                    "parameters": {"pid": "not-a-number"},
                }
            ],
        }
        res = self.validator.validate(bad_dict)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("expects type 'number', got str" in err for err in res.errors))

    def test_invalid_parameters_unknown_extra_param(self):
        # filesystem.hash takes 'path', extra 'algorithm' is unknown
        bad_dict = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Extra Param Test",
            "operations": [
                {
                    "id": "op-001",
                    "type": "filesystem.hash",
                    "parameters": {
                        "path": "./evidence",
                        "extra_unsupported": 123,
                    },
                }
            ],
        }
        res = self.validator.validate(bad_dict)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Unknown parameter 'extra_unsupported'" in err for err in res.errors))

    def test_empty_parameters_and_parameterized_operation(self):
        op1 = IROperation(id="op-001", type="system.info", parameters={})
        op2 = IROperation(id="op-002", type="filesystem.hash", parameters={"path": "./evidence"})
        doc = IRDocument(
            investigation="Param Test",
            operations=[op1, op2],
        )
        res = self.validator.validate(doc)
        self.assertTrue(res.is_valid)

    def test_file_serialization_round_trip(self):
        op = IROperation(id="op-001", type="processes.details", parameters={"pid": 1024})
        doc = IRDocument(investigation="File Test", operations=[op])

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.ir.json")
            doc.to_file(filepath)

            self.assertTrue(os.path.isfile(filepath))
            loaded_doc = IRDocument.from_file(filepath)

            self.assertEqual(loaded_doc.investigation, "File Test")
            self.assertEqual(len(loaded_doc.operations), 1)
            self.assertEqual(loaded_doc.operations[0].id, "op-001")
            self.assertEqual(loaded_doc.operations[0].parameters, {"pid": 1024})

            # Validate loaded document
            val_res = validate_ir(loaded_doc)
            self.assertTrue(val_res.is_valid)


if __name__ == "__main__":
    unittest.main()
