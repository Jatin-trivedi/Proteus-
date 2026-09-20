"""
Unit and Integration Tests for Network Forensic Collectors (Priority 4.4)
- network.interfaces()
- network.connections()
- network.routes()
- network.dns()
"""

import unittest
from unittest.mock import patch

from runtime.collectors.network import (
    NetworkInterfacesCollector,
    NetworkConnectionsCollector,
    NetworkRoutesCollector,
    NetworkDnsCollector,
)
from runtime.registry import create_default_registry
from runtime.dispatcher import OperationDispatcher


class TestNetworkCollectors(unittest.TestCase):

    def setUp(self):
        self.interfaces_collector = NetworkInterfacesCollector()
        self.connections_collector = NetworkConnectionsCollector()
        self.routes_collector = NetworkRoutesCollector()
        self.dns_collector = NetworkDnsCollector()
        self.dispatcher = OperationDispatcher(create_default_registry())

    def test_network_interfaces_success_and_schema(self):
        """Verify network.interfaces returns valid list of network adapters matching schema."""
        data = self.interfaces_collector.collect({})
        self.assertIsInstance(data, dict)
        self.assertIn("interfaces", data)
        self.assertIsInstance(data["interfaces"], list)
        self.assertTrue(len(data["interfaces"]) > 0)

        for iface in data["interfaces"]:
            self.assertIn("name", iface)
            self.assertIn("addresses", iface)
            self.assertIn("mac", iface)
            self.assertIsInstance(iface["name"], str)
            self.assertIsInstance(iface["addresses"], list)
            self.assertIsInstance(iface["mac"], str)

    def test_network_connections_success_and_schema(self):
        """Verify network.connections returns list of sockets/connections matching schema."""
        data = self.connections_collector.collect({})
        self.assertIsInstance(data, dict)
        self.assertIn("connections", data)
        self.assertIsInstance(data["connections"], list)

        for conn in data["connections"][:10]:
            self.assertIn("protocol", conn)
            self.assertIn("local", conn)
            self.assertIn("remote", conn)
            self.assertIn("state", conn)
            self.assertIn("pid", conn)
            self.assertIsInstance(conn["protocol"], str)
            self.assertIsInstance(conn["local"], str)
            self.assertIsInstance(conn["remote"], str)
            self.assertIsInstance(conn["state"], str)
            self.assertIsInstance(conn["pid"], int)

    def test_network_routes_success_and_schema(self):
        """Verify network.routes returns routing table matching schema."""
        data = self.routes_collector.collect({})
        self.assertIsInstance(data, dict)
        self.assertIn("routes", data)
        self.assertIsInstance(data["routes"], list)
        self.assertTrue(len(data["routes"]) > 0)

        for route in data["routes"]:
            self.assertIn("destination", route)
            self.assertIn("gateway", route)
            self.assertIn("interface", route)
            self.assertIn("metric", route)
            self.assertIsInstance(route["destination"], str)
            self.assertIsInstance(route["gateway"], str)
            self.assertIsInstance(route["interface"], str)
            self.assertIsInstance(route["metric"], int)

    def test_network_dns_success_and_schema(self):
        """Verify network.dns returns DNS configuration matching schema."""
        data = self.dns_collector.collect({})
        self.assertIsInstance(data, dict)
        self.assertIn("dns_servers", data)
        self.assertIn("search_domains", data)
        self.assertIn("configuration", data)
        self.assertIsInstance(data["dns_servers"], list)
        self.assertIsInstance(data["search_domains"], list)
        self.assertIsInstance(data["configuration"], dict)

    def test_network_interfaces_fallback_on_failure(self):
        """Verify network.interfaces falls back to loopback if command fails."""
        with patch("subprocess.check_output", side_effect=Exception("Command failed")):
            collector = NetworkInterfacesCollector()
            data = collector.collect({})
            self.assertIn("interfaces", data)
            self.assertEqual(len(data["interfaces"]), 1)
            self.assertEqual(data["interfaces"][0]["name"], "lo0")

    def test_network_routes_fallback_on_failure(self):
        """Verify network.routes falls back to default localhost route if command fails."""
        with patch("subprocess.check_output", side_effect=Exception("Command failed")):
            collector = NetworkRoutesCollector()
            data = collector.collect({})
            self.assertIn("routes", data)
            self.assertEqual(len(data["routes"]), 1)
            self.assertEqual(data["routes"][0]["destination"], "default")

    def test_network_dns_empty_fallback_on_missing_config(self):
        """Verify network.dns handles missing config files gracefully without crashing."""
        with patch("os.path.exists", return_value=False):
            with patch("subprocess.check_output", side_effect=Exception("No scutil")):
                collector = NetworkDnsCollector()
                data = collector.collect({})
                self.assertEqual(data["dns_servers"], [])
                self.assertEqual(data["search_domains"], [])
                self.assertEqual(data["configuration"], {})

    def test_dispatcher_network_investigation_e2e(self):
        """Verify complete execution of an all-network investigation IR document."""
        ir_doc = {
            "version": "1.0",
            "ir_type": "jocky_forensic_ir",
            "investigation": "Network Forensic Triage",
            "operations": [
                {"id": "op-001", "type": "network.interfaces", "parameters": {}},
                {"id": "op-002", "type": "network.connections", "parameters": {}},
                {"id": "op-003", "type": "network.routes", "parameters": {}},
                {"id": "op-004", "type": "network.dns", "parameters": {}},
            ]
        }

        exec_res = self.dispatcher.dispatch(ir_doc)
        self.assertEqual(exec_res.investigation, "Network Forensic Triage")
        self.assertEqual(len(exec_res.results), 4)

        # All 4 operations should succeed
        for i, expected_type in enumerate([
            "network.interfaces",
            "network.connections",
            "network.routes",
            "network.dns",
        ]):
            res = exec_res.results[i]
            self.assertEqual(res.operation_id, f"op-{i+1:03d}")
            self.assertEqual(res.type, expected_type)
            self.assertEqual(res.status, "success")
            self.assertIsNone(res.error)
            self.assertIsNotNone(res.data)


if __name__ == "__main__":
    unittest.main()
