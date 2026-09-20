"""
Unit Tests for Forensic Function Registry
"""
import unittest
from compiler.semantic.registry import ForensicFunctionRegistry, DEFAULT_REGISTRY


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = DEFAULT_REGISTRY

    def test_valid_namespaces(self):
        namespaces = self.registry.get_all_namespaces()
        self.assertEqual(namespaces, ["filesystem", "network", "processes", "system"])
        self.assertTrue(self.registry.has_namespace("system"))
        self.assertTrue(self.registry.has_namespace("processes"))
        self.assertTrue(self.registry.has_namespace("network"))
        self.assertTrue(self.registry.has_namespace("filesystem"))
        self.assertFalse(self.registry.has_namespace("storage"))

    def test_valid_functions_and_categories(self):
        # System
        self.assertTrue(self.registry.has_function("system", "info"))
        self.assertTrue(self.registry.has_function("system", "users"))
        sys_info = self.registry.get_function_spec("system", "info")
        self.assertEqual(sys_info.category, "system")
        self.assertEqual(sys_info.min_args, 0)

        # Processes
        self.assertTrue(self.registry.has_function("processes", "list"))
        self.assertTrue(self.registry.has_function("processes", "details"))
        proc_det = self.registry.get_function_spec("processes", "details")
        self.assertEqual(proc_det.category, "process")
        self.assertEqual(proc_det.min_args, 1)
        self.assertEqual(proc_det.arguments[0].type, "number")

        # Network
        self.assertTrue(self.registry.has_function("network", "interfaces"))
        self.assertTrue(self.registry.has_function("network", "connections"))
        self.assertTrue(self.registry.has_function("network", "routes"))
        self.assertTrue(self.registry.has_function("network", "dns"))
        net_conn = self.registry.get_function_spec("network", "connections")
        self.assertEqual(net_conn.category, "network")

        # Filesystem
        self.assertTrue(self.registry.has_function("filesystem", "metadata"))
        self.assertTrue(self.registry.has_function("filesystem", "hash"))
        fs_hash = self.registry.get_function_spec("filesystem", "hash")
        self.assertEqual(fs_hash.category, "filesystem")
        self.assertEqual(fs_hash.min_args, 1)
        self.assertEqual(fs_hash.arguments[0].type, "string")

    def test_unknown_functions(self):
        self.assertFalse(self.registry.has_function("system", "fakeFunction"))
        self.assertFalse(self.registry.has_function("network", "fake"))


if __name__ == "__main__":
    unittest.main()
