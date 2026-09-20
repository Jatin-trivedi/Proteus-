"""
Unit and Integration Tests for System Forensic Collectors (Priority 4.2)
- system.info()
- system.users()
"""

import unittest
import platform
import socket
from unittest.mock import patch

from runtime.collectors.system import SystemInfoCollector, SystemUsersCollector, _get_uptime_string, _get_current_username
from runtime.registry import create_default_registry
from runtime.dispatcher import OperationDispatcher
from runtime.models import OperationResult, ExecutionResult


class TestSystemCollectors(unittest.TestCase):

    def setUp(self):
        self.info_collector = SystemInfoCollector()
        self.users_collector = SystemUsersCollector()
        self.dispatcher = OperationDispatcher(create_default_registry())

    def test_system_info_success_and_schema(self):
        """Verify system.info collects valid non-empty values matching the exact schema."""
        data = self.info_collector.collect({})
        self.assertIsInstance(data, dict)

        # Check required schema keys
        required_keys = {"hostname", "os", "architecture", "kernel", "uptime", "username"}
        self.assertEqual(set(data.keys()), required_keys)

        # Structural assertions on types and content
        for key in required_keys:
            self.assertIsInstance(data[key], str)
            self.assertTrue(len(data[key]) > 0, f"Field '{key}' should not be empty")

        # Uptime should end with 's'
        self.assertTrue(data["uptime"].endswith("s"))

    def test_system_users_success_and_schema(self):
        """Verify system.users collects user list matching the required schema."""
        data = self.users_collector.collect({})
        self.assertIsInstance(data, dict)
        self.assertIn("users", data)
        self.assertIsInstance(data["users"], list)

        # Each user entry must have 'name' and 'type': 'local'
        for user in data["users"]:
            self.assertIsInstance(user, dict)
            self.assertIn("name", user)
            self.assertIn("type", user)
            self.assertEqual(user["type"], "local")
            self.assertIsInstance(user["name"], str)
            self.assertTrue(len(user["name"]) > 0)

    def test_system_users_empty_fallback_to_current_user(self):
        """Verify that if user enumeration yields no accounts, fallback to current user occurs."""
        with patch("runtime.collectors.system.pwd", create=True, side_effect=ImportError):
            with patch("platform.system", return_value="CustomOS"):
                collector = SystemUsersCollector()
                data = collector.collect({})
                self.assertIn("users", data)
                self.assertTrue(len(data["users"]) >= 1)
                self.assertEqual(data["users"][0]["type"], "local")

    def test_system_users_permission_error_handling(self):
        """Verify that permission errors during user enumeration are handled gracefully."""
        with patch("pwd.getpwall", side_effect=PermissionError("Access denied")):
            collector = SystemUsersCollector()
            # Should not raise exception
            data = collector.collect({})
            self.assertIn("users", data)
            self.assertIsInstance(data["users"], list)

    def test_dispatcher_system_info_integration(self):
        """Verify dispatcher invokes system.info and returns structured OperationResult."""
        op = {
            "id": "op-001",
            "type": "system.info",
            "parameters": {}
        }
        res = self.dispatcher.dispatch_operation(op)

        self.assertEqual(res.operation_id, "op-001")
        self.assertEqual(res.type, "system.info")
        self.assertEqual(res.status, "success")
        self.assertIsNone(res.error)
        self.assertIn("hostname", res.data)
        self.assertIn("os", res.data)
        self.assertIn("architecture", res.data)
        self.assertIn("kernel", res.data)
        self.assertIn("uptime", res.data)
        self.assertIn("username", res.data)

    def test_dispatcher_system_users_integration(self):
        """Verify dispatcher invokes system.users and returns structured OperationResult."""
        op = {
            "id": "op-002",
            "type": "system.users",
            "parameters": {}
        }
        res = self.dispatcher.dispatch_operation(op)

        self.assertEqual(res.operation_id, "op-002")
        self.assertEqual(res.type, "system.users")
        self.assertEqual(res.status, "success")
        self.assertIsNone(res.error)
        self.assertIn("users", res.data)
        self.assertIsInstance(res.data["users"], list)

    def test_dispatcher_end_to_end_system_investigation(self):
        """Verify complete execution of a system investigation IR document."""
        ir_doc = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "System Baseline Triage",
            "operations": [
                {
                    "id": "op-001",
                    "type": "system.info",
                    "parameters": {}
                },
                {
                    "id": "op-002",
                    "type": "system.users",
                    "parameters": {}
                }
            ]
        }

        exec_res = self.dispatcher.dispatch(ir_doc)
        self.assertEqual(exec_res.investigation, "System Baseline Triage")
        self.assertEqual(len(exec_res.results), 2)

        # Check Op 1
        self.assertEqual(exec_res.results[0].operation_id, "op-001")
        self.assertEqual(exec_res.results[0].type, "system.info")
        self.assertEqual(exec_res.results[0].status, "success")
        self.assertIn("os", exec_res.results[0].data)

        # Check Op 2
        self.assertEqual(exec_res.results[1].operation_id, "op-002")
        self.assertEqual(exec_res.results[1].type, "system.users")
        self.assertEqual(exec_res.results[1].status, "success")
        self.assertIn("users", exec_res.results[1].data)


if __name__ == "__main__":
    unittest.main()
