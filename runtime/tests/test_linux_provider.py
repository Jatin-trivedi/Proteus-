"""
Unit tests for Linux Platform Providers (Mocked)
"""

import unittest
from unittest.mock import mock_open, patch

from runtime.errors import CollectorException, ErrorCode
from runtime.providers.linux import (
    LinuxNetworkProvider,
    LinuxProcessProvider,
    LinuxSystemProvider,
)


class TestLinuxProvider(unittest.TestCase):

    def test_linux_system_provider_uptime_procfs(self):
        provider = LinuxSystemProvider()
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="12345.67 89012.34\n")):
                uptime = provider.get_uptime()
                self.assertEqual(uptime, "12345s")

    def test_linux_system_provider_users(self):
        provider = LinuxSystemProvider()
        users = provider.get_users()
        self.assertIsInstance(users, list)
        self.assertTrue(len(users) > 0)
        self.assertEqual(users[0]["type"], "local")

    def test_linux_process_provider_list_processes(self):
        provider = LinuxProcessProvider()
        sample_ps_out = b"  1   0 root   /sbin/launchd\n 1234 1000 alice  /usr/bin/python3\n"
        with patch("subprocess.check_output", return_value=sample_ps_out):
            procs = provider.list_processes()
            self.assertEqual(len(procs), 2)
            self.assertEqual(procs[0]["pid"], 1)
            self.assertEqual(procs[0]["username"], "root")
            self.assertEqual(procs[1]["pid"], 1234)
            self.assertEqual(procs[1]["name"], "/usr/bin/python3")

    def test_linux_process_provider_details(self):
        provider = LinuxProcessProvider()
        sample_ps_out = b" 1234 1000 Sun Sep 20 12:00:00 2026 /usr/bin/python3 -m unittest\n"
        with patch("subprocess.check_output", return_value=sample_ps_out):
            details = provider.get_process_details(1234)
            self.assertEqual(details["pid"], 1234)
            self.assertEqual(details["parent_pid"], 1000)
            self.assertEqual(details["executable"], "/usr/bin/python3 -m unittest")

    def test_linux_network_provider_routes_ip_route(self):
        provider = LinuxNetworkProvider()
        sample_ip_route = b"default via 192.168.1.1 dev eth0 metric 100\n192.168.1.0/24 dev eth0 scope link\n"
        with patch("subprocess.check_output", return_value=sample_ip_route):
            routes = provider.get_routes()
            self.assertEqual(len(routes), 2)
            self.assertEqual(routes[0]["destination"], "default")
            self.assertEqual(routes[0]["gateway"], "192.168.1.1")
            self.assertEqual(routes[0]["interface"], "eth0")
            self.assertEqual(routes[0]["metric"], 100)

    def test_linux_network_provider_dns_resolv_conf(self):
        provider = LinuxNetworkProvider()
        sample_resolv = "nameserver 1.1.1.1\nnameserver 8.8.8.8\nsearch localdomain corp\n"
        with patch("platform.system", return_value="Linux"):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=sample_resolv)):
                    dns = provider.get_dns()
                    self.assertEqual(dns["dns_servers"], ["1.1.1.1", "8.8.8.8"])
                    self.assertEqual(dns["search_domains"], ["localdomain", "corp"])
                    self.assertEqual(dns["configuration"]["source"], "/etc/resolv.conf")


if __name__ == "__main__":
    unittest.main()
