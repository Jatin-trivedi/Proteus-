"""
Unit and Integration Tests for Filesystem Forensic Collectors (Priority 4.5)
- filesystem.metadata(path)
- filesystem.hash(path)
"""

import os
import tempfile
import hashlib
import unittest
from unittest.mock import patch

from runtime.collectors.filesystem import FilesystemMetadataCollector, FilesystemHashCollector
from runtime.registry import create_default_registry
from runtime.dispatcher import OperationDispatcher
from runtime.errors import ErrorCode, CollectorException


class TestFilesystemCollectors(unittest.TestCase):

    def setUp(self):
        self.metadata_collector = FilesystemMetadataCollector()
        self.hash_collector = FilesystemHashCollector()
        self.dispatcher = OperationDispatcher(create_default_registry())

        # Create temporary test file with known deterministic content
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_content = b"Proteus Forensic IR - Deterministic Content for Testing SHA256\n"
        self.expected_sha256 = hashlib.sha256(self.test_content).hexdigest()
        self.test_file_path = os.path.join(self.test_dir.name, "evidence.dat")
        with open(self.test_file_path, "wb") as f:
            f.write(self.test_content)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_filesystem_metadata_success_and_schema(self):
        """Verify filesystem.metadata returns correct schema for existing test file."""
        data = self.metadata_collector.collect({"path": self.test_file_path})

        self.assertIsInstance(data, dict)
        required_keys = {"path", "size", "creation_time", "modification_time", "access_time", "permissions"}
        self.assertEqual(set(data.keys()), required_keys)

        self.assertEqual(data["path"], self.test_file_path)
        self.assertEqual(data["size"], len(self.test_content))
        self.assertIsInstance(data["creation_time"], str)
        self.assertIsInstance(data["modification_time"], str)
        self.assertIsInstance(data["access_time"], str)
        self.assertIsInstance(data["permissions"], str)

    def test_filesystem_hash_known_content(self):
        """Verify filesystem.hash computes exact SHA-256 digest for known content."""
        data = self.hash_collector.collect({"path": self.test_file_path})

        self.assertIsInstance(data, dict)
        self.assertEqual(data["path"], self.test_file_path)
        self.assertEqual(data["algorithm"], "SHA-256")
        self.assertEqual(data["hash"], self.expected_sha256)

    def test_filesystem_hash_consistency(self):
        """Verify that multiple consecutive hash calculations yield identical digests."""
        hash1 = self.hash_collector.collect({"path": self.test_file_path})["hash"]
        hash2 = self.hash_collector.collect({"path": self.test_file_path})["hash"]
        self.assertEqual(hash1, hash2)
        self.assertEqual(hash1, self.expected_sha256)

    def test_missing_file_metadata_and_hash(self):
        """Verify non-existent path raises structured CollectorException on metadata and hash."""
        non_existent_path = os.path.join(self.test_dir.name, "ghost_file.bin")

        # Metadata
        with self.assertRaises(CollectorException) as cm_meta:
            self.metadata_collector.collect({"path": non_existent_path})
        self.assertEqual(cm_meta.exception.code, ErrorCode.COLLECTION_FAILED)
        self.assertIn("not found", cm_meta.exception.message.lower())

        # Hash
        with self.assertRaises(CollectorException) as cm_hash:
            self.hash_collector.collect({"path": non_existent_path})
        self.assertEqual(cm_hash.exception.code, ErrorCode.COLLECTION_FAILED)
        self.assertIn("not found", cm_hash.exception.message.lower())

    def test_missing_or_invalid_path_parameters(self):
        """Verify missing or invalid path parameters raise INVALID_PARAMETERS exception."""
        for collector in (self.metadata_collector, self.hash_collector):
            # Missing parameter
            with self.assertRaises(CollectorException) as cm1:
                collector.collect({})
            self.assertEqual(cm1.exception.code, ErrorCode.INVALID_PARAMETERS)

            # Non-string parameter
            with self.assertRaises(CollectorException) as cm2:
                collector.collect({"path": 12345})
            self.assertEqual(cm2.exception.code, ErrorCode.INVALID_PARAMETERS)

            # Empty string parameter
            with self.assertRaises(CollectorException) as cm3:
                collector.collect({"path": "   "})
            self.assertEqual(cm3.exception.code, ErrorCode.INVALID_PARAMETERS)

    def test_permission_denied_handling(self):
        """Verify permission errors raise structured PERMISSION_DENIED exception."""
        with patch("os.path.exists", return_value=True):
            with patch("os.stat", side_effect=PermissionError("Access denied")):
                with self.assertRaises(CollectorException) as cm_meta:
                    self.metadata_collector.collect({"path": self.test_file_path})
                self.assertEqual(cm_meta.exception.code, ErrorCode.PERMISSION_DENIED)

            with patch("builtins.open", side_effect=PermissionError("Access denied")):
                with self.assertRaises(CollectorException) as cm_hash:
                    self.hash_collector.collect({"path": self.test_file_path})
                self.assertEqual(cm_hash.exception.code, ErrorCode.PERMISSION_DENIED)


    def test_dispatcher_complete_investigation_e2e(self):
        """Verify complete investigation containing metadata and hash operations through dispatcher."""
        ir_doc = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Evidence File Integrity Check",
            "operations": [
                {
                    "id": "op-001",
                    "type": "filesystem.metadata",
                    "parameters": {"path": self.test_file_path}
                },
                {
                    "id": "op-002",
                    "type": "filesystem.hash",
                    "parameters": {"path": self.test_file_path}
                }
            ]
        }

        exec_res = self.dispatcher.dispatch(ir_doc)
        self.assertEqual(exec_res.investigation, "Evidence File Integrity Check")
        self.assertEqual(len(exec_res.results), 2)

        # Op 1: Metadata
        self.assertEqual(exec_res.results[0].operation_id, "op-001")
        self.assertEqual(exec_res.results[0].type, "filesystem.metadata")
        self.assertEqual(exec_res.results[0].status, "success")
        self.assertEqual(exec_res.results[0].data["size"], len(self.test_content))

        # Op 2: Hash
        self.assertEqual(exec_res.results[1].operation_id, "op-002")
        self.assertEqual(exec_res.results[1].type, "filesystem.hash")
        self.assertEqual(exec_res.results[1].status, "success")
        self.assertEqual(exec_res.results[1].data["hash"], self.expected_sha256)


if __name__ == "__main__":
    unittest.main()
