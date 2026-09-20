"""
Unit and Integration Tests for Process Forensic Collectors (Priority 4.3)
- processes.list()
- processes.details(pid)
"""

import os
import unittest
from unittest.mock import patch

from runtime.collectors.processes import ProcessesListCollector, ProcessesDetailsCollector
from runtime.registry import create_default_registry
from runtime.dispatcher import OperationDispatcher
from runtime.errors import ErrorCode, CollectorException


class TestProcessCollectors(unittest.TestCase):

    def setUp(self):
        self.list_collector = ProcessesListCollector()
        self.details_collector = ProcessesDetailsCollector()
        self.dispatcher = OperationDispatcher(create_default_registry())

    def test_processes_list_success_and_schema(self):
        """Verify processes.list collects running processes matching the required schema."""
        data = self.list_collector.collect({})
        self.assertIsInstance(data, dict)
        self.assertIn("processes", data)
        self.assertIsInstance(data["processes"], list)
        self.assertTrue(len(data["processes"]) > 0)

        # Check schema of each process entry
        for proc in data["processes"][:10]:
            self.assertIn("pid", proc)
            self.assertIn("name", proc)
            self.assertIn("parent_pid", proc)
            self.assertIn("username", proc)
            self.assertIsInstance(proc["pid"], int)
            self.assertIsInstance(proc["name"], str)
            self.assertIsInstance(proc["parent_pid"], int)
            self.assertIsInstance(proc["username"], str)

    def test_processes_details_current_process(self):
        """Verify processes.details for the current process PID."""
        curr_pid = os.getpid()
        data = self.details_collector.collect({"pid": curr_pid})

        self.assertIsInstance(data, dict)
        self.assertEqual(data["pid"], curr_pid)
        self.assertIn("name", data)
        self.assertIn("parent_pid", data)
        self.assertIn("start_time", data)
        self.assertIn("executable", data)
        self.assertIsInstance(data["name"], str)
        self.assertIsInstance(data["parent_pid"], int)
        self.assertIsInstance(data["start_time"], str)
        self.assertIsInstance(data["executable"], str)

    def test_processes_details_nonexistent_pid(self):
        """Verify processes.details for a non-existent PID raises structured CollectorException."""
        non_existent_pid = 9999999
        with self.assertRaises(CollectorException) as cm:
            self.details_collector.collect({"pid": non_existent_pid})

        self.assertIn(cm.exception.code, [ErrorCode.COLLECTION_FAILED, ErrorCode.PERMISSION_DENIED])
        self.assertIn(str(non_existent_pid), cm.exception.message)

    def test_processes_details_missing_or_invalid_pid_parameter(self):
        """Verify processes.details with missing or invalid pid parameter raises INVALID_PARAMETERS."""
        # Missing PID
        with self.assertRaises(CollectorException) as cm1:
            self.details_collector.collect({})
        self.assertEqual(cm1.exception.code, ErrorCode.INVALID_PARAMETERS)

        # Invalid PID (non-integer string)
        with self.assertRaises(CollectorException) as cm2:
            self.details_collector.collect({"pid": "invalid_pid_string"})
        self.assertEqual(cm2.exception.code, ErrorCode.INVALID_PARAMETERS)

    def test_dispatcher_processes_list_integration(self):
        """Verify dispatcher invokes processes.list and returns structured OperationResult."""
        op = {
            "id": "op-001",
            "type": "processes.list",
            "parameters": {}
        }
        res = self.dispatcher.dispatch_operation(op)

        self.assertEqual(res.operation_id, "op-001")
        self.assertEqual(res.type, "processes.list")
        self.assertEqual(res.status, "success")
        self.assertIsNone(res.error)
        self.assertIn("processes", res.data)
        self.assertIsInstance(res.data["processes"], list)

    def test_dispatcher_processes_details_integration(self):
        """Verify dispatcher invokes processes.details and returns structured OperationResult."""
        curr_pid = os.getpid()
        op = {
            "id": "op-002",
            "type": "processes.details",
            "parameters": {"pid": curr_pid}
        }
        res = self.dispatcher.dispatch_operation(op)

        self.assertEqual(res.operation_id, "op-002")
        self.assertEqual(res.type, "processes.details")
        self.assertEqual(res.status, "success")
        self.assertIsNone(res.error)
        self.assertEqual(res.data["pid"], curr_pid)
        self.assertIn("executable", res.data)

    def test_dispatcher_failed_operation_does_not_stop_next(self):
        """Verify that a failing processes.details operation does not stop subsequent operations."""
        curr_pid = os.getpid()
        ir_doc = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Process Triage Investigation",
            "operations": [
                {
                    "id": "op-001",
                    "type": "processes.list",
                    "parameters": {}
                },
                {
                    "id": "op-002",
                    "type": "processes.details",
                    "parameters": {"pid": 9999999}  # Non-existent PID
                },
                {
                    "id": "op-003",
                    "type": "processes.details",
                    "parameters": {"pid": curr_pid}  # Valid PID
                }
            ]
        }

        exec_res = self.dispatcher.dispatch(ir_doc)
        self.assertEqual(len(exec_res.results), 3)

        # Op 1: Success
        self.assertEqual(exec_res.results[0].operation_id, "op-001")
        self.assertEqual(exec_res.results[0].status, "success")
        self.assertIn("processes", exec_res.results[0].data)

        # Op 2: Error (Isolated)
        self.assertEqual(exec_res.results[1].operation_id, "op-002")
        self.assertEqual(exec_res.results[1].status, "error")
        self.assertIsNotNone(exec_res.results[1].error)
        self.assertIn(exec_res.results[1].error.code, [ErrorCode.COLLECTION_FAILED, ErrorCode.PERMISSION_DENIED])

        # Op 3: Success (Executed after Op 2 failure!)
        self.assertEqual(exec_res.results[2].operation_id, "op-003")
        self.assertEqual(exec_res.results[2].status, "success")
        self.assertEqual(exec_res.results[2].data["pid"], curr_pid)


if __name__ == "__main__":
    unittest.main()
