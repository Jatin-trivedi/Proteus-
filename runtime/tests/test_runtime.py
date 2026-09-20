"""
Unit and Integration Tests for Proteus JOCKY Forensic Runtime (Priority 4.1)
"""

import unittest
import json
from typing import Dict, Any

from runtime.errors import StructuredError, ErrorCode, CollectorException
from runtime.models import OperationResult, ExecutionResult
from runtime.collector import BaseCollector, PlaceholderCollector
from runtime.registry import OperationRegistry, create_default_registry, APPROVED_OPERATIONS
from runtime.dispatcher import OperationDispatcher


class MockSuccessCollector(BaseCollector):
    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(self.data)
        if parameters:
            result["echo_params"] = parameters
        return result


class MockFailingCollector(BaseCollector):
    def __init__(self, code: str = ErrorCode.COLLECTION_FAILED, message: str = "Collector crashed"):
        self.code = code
        self.message = message

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        raise CollectorException(code=self.code, message=self.message)


class MockCrashCollector(BaseCollector):
    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError("Unexpected OS failure")


class TestForensicRuntime(unittest.TestCase):

    def test_approved_operations_allowlist(self):
        """Verify that exactly the 10 approved MVP operations are in the allowlist."""
        expected = {
            "system.info",
            "system.users",
            "processes.list",
            "processes.details",
            "network.interfaces",
            "network.connections",
            "network.routes",
            "network.dns",
            "filesystem.metadata",
            "filesystem.hash",
        }
        self.assertEqual(APPROVED_OPERATIONS, expected)

    def test_registry_lookup_and_placeholders(self):
        """Verify registry initialization with all 10 implemented approved forensic collectors."""
        registry = create_default_registry()
        for op in APPROVED_OPERATIONS:
            self.assertTrue(registry.is_registered(op))
            self.assertTrue(registry.is_approved(op))
            collector = registry.get(op)
            self.assertIsInstance(collector, BaseCollector)
            self.assertNotIsInstance(collector, PlaceholderCollector)

    def test_registry_rejects_unapproved_operations(self):
        """Verify that unapproved operation types cannot be registered."""
        registry = OperationRegistry()
        with self.assertRaises(ValueError):
            registry.register("arbitrary.exec", MockSuccessCollector({}))

        with self.assertRaises(ValueError):
            registry.register("system.hack", MockSuccessCollector({}))

    def test_placeholder_collector_raises_not_implemented(self):
        """Verify placeholder collector raises structured NOT_IMPLEMENTED exception."""
        placeholder = PlaceholderCollector("system.info")
        with self.assertRaises(CollectorException) as cm:
            placeholder.collect({})
        self.assertEqual(cm.exception.code, ErrorCode.NOT_IMPLEMENTED)
        self.assertIn("system.info", str(cm.exception))

    def test_result_format_success(self):
        """Verify structured result format on success matching specification."""
        result = OperationResult(
            operation_id="op-001",
            type="system.info",
            status="success",
            data={"hostname": "sec-node-1", "os": "Linux"},
            error=None
        )
        d = result.to_dict()
        self.assertEqual(d["operation_id"], "op-001")
        self.assertEqual(d["type"], "system.info")
        self.assertEqual(d["status"], "success")
        self.assertEqual(d["data"], {"hostname": "sec-node-1", "os": "Linux"})
        self.assertIsNone(d["error"])

        # JSON serialization
        js = result.to_json()
        self.assertIn('"status": "success"', js)
        self.assertIn('"error": null', js)

    def test_result_format_error(self):
        """Verify structured result format on failure matching specification."""
        result = OperationResult(
            operation_id="op-002",
            type="processes.details",
            status="error",
            data=None,
            error=StructuredError(code="COLLECTION_FAILED", message="PID 9999 not found")
        )
        d = result.to_dict()
        self.assertEqual(d["operation_id"], "op-002")
        self.assertEqual(d["type"], "processes.details")
        self.assertEqual(d["status"], "error")
        self.assertIsNone(d["data"])
        self.assertEqual(d["error"], {
            "code": "COLLECTION_FAILED",
            "message": "PID 9999 not found"
        })

    def test_dispatcher_unknown_operation(self):
        """Verify dispatcher rejects unknown or unallowlisted operations."""
        dispatcher = OperationDispatcher(create_default_registry())
        op = {"id": "op-001", "type": "arbitrary.command", "parameters": {}}
        res = dispatcher.dispatch_operation(op)

        self.assertEqual(res.status, "error")
        self.assertEqual(res.error.code, ErrorCode.UNKNOWN_OPERATION)
        self.assertIsNone(res.data)

    def test_dispatcher_with_registered_collector(self):
        """Verify dispatcher invokes registered collector and returns data."""
        registry = create_default_registry()
        registry.register("system.info", MockSuccessCollector({"hostname": "test-box"}))
        dispatcher = OperationDispatcher(registry)

        op = {"id": "op-001", "type": "system.info", "parameters": {}}
        res = dispatcher.dispatch_operation(op)

        self.assertEqual(res.status, "success")
        self.assertEqual(res.data, {"hostname": "test-box"})
        self.assertIsNone(res.error)

    def test_dispatcher_multiple_operations_and_deterministic_order(self):
        """Verify dispatcher processes multiple operations preserving strict sequential order."""
        registry = create_default_registry()
        registry.register("system.info", MockSuccessCollector({"node": "workstation"}))
        registry.register("network.connections", MockSuccessCollector({"connections": []}))
        registry.register("filesystem.metadata", MockSuccessCollector({"size": 4096}))
        dispatcher = OperationDispatcher(registry)

        ir_doc = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Tri-Phase Triage",
            "operations": [
                {"id": "op-001", "type": "system.info", "parameters": {}},
                {"id": "op-002", "type": "network.connections", "parameters": {}},
                {"id": "op-003", "type": "filesystem.metadata", "parameters": {"path": "/tmp"}}
            ]
        }

        exec_res = dispatcher.dispatch(ir_doc)
        self.assertEqual(exec_res.investigation, "Tri-Phase Triage")
        self.assertEqual(len(exec_res.results), 3)

        # Ordering check
        self.assertEqual(exec_res.results[0].operation_id, "op-001")
        self.assertEqual(exec_res.results[0].type, "system.info")
        self.assertEqual(exec_res.results[0].status, "success")

        self.assertEqual(exec_res.results[1].operation_id, "op-002")
        self.assertEqual(exec_res.results[1].type, "network.connections")
        self.assertEqual(exec_res.results[1].status, "success")

        self.assertEqual(exec_res.results[2].operation_id, "op-003")
        self.assertEqual(exec_res.results[2].type, "filesystem.metadata")
        self.assertEqual(exec_res.results[2].status, "success")
        self.assertEqual(exec_res.results[2].data["echo_params"], {"path": "/tmp"})

    def test_one_failure_does_not_stop_remaining_operations(self):
        """Verify that when one operation fails, subsequent operations still execute and succeed."""
        registry = create_default_registry()
        registry.register("system.info", MockSuccessCollector({"node": "workstation"}))
        registry.register("processes.details", MockFailingCollector(ErrorCode.PERMISSION_DENIED, "Access denied to PID 1"))
        registry.register("network.dns", MockSuccessCollector({"dns_servers": ["8.8.8.8"]}))
        dispatcher = OperationDispatcher(registry)

        ir_doc = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Fault Tolerance Test",
            "operations": [
                {"id": "op-001", "type": "system.info", "parameters": {}},
                {"id": "op-002", "type": "processes.details", "parameters": {"pid": 1}},
                {"id": "op-003", "type": "network.dns", "parameters": {}}
            ]
        }

        exec_res = dispatcher.dispatch(ir_doc)
        self.assertEqual(len(exec_res.results), 3)

        # Op 1: Success
        self.assertEqual(exec_res.results[0].operation_id, "op-001")
        self.assertEqual(exec_res.results[0].status, "success")

        # Op 2: Error
        self.assertEqual(exec_res.results[1].operation_id, "op-002")
        self.assertEqual(exec_res.results[1].status, "error")
        self.assertEqual(exec_res.results[1].error.code, ErrorCode.PERMISSION_DENIED)
        self.assertIn("Access denied", exec_res.results[1].error.message)

        # Op 3: Success (executed despite Op 2 error!)
        self.assertEqual(exec_res.results[2].operation_id, "op-003")
        self.assertEqual(exec_res.results[2].status, "success")
        self.assertEqual(exec_res.results[2].data["dns_servers"], ["8.8.8.8"])

    def test_unexpected_runtime_exception_handled_gracefully(self):
        """Verify that unhandled collector exceptions are trapped as COLLECTION_FAILED without crashing."""
        registry = create_default_registry()
        registry.register("system.info", MockCrashCollector())
        dispatcher = OperationDispatcher(registry)

        op = {"id": "op-001", "type": "system.info", "parameters": {}}
        res = dispatcher.dispatch_operation(op)

        self.assertEqual(res.status, "error")
        self.assertEqual(res.error.code, ErrorCode.COLLECTION_FAILED)
        self.assertIn("Unexpected OS failure", res.error.message)


if __name__ == "__main__":
    unittest.main()
