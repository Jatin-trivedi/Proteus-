"""
Unit tests for Windows Platform Providers (Mocked)
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

from runtime.errors import CollectorException, ErrorCode
from runtime.providers.windows import (
    WindowsNetworkProvider,
    WindowsProcessProvider,
    WindowsSystemProvider,
)


class TestWindowsProvider(unittest.TestCase):

    def test_windows_system_provider_uptime_ctypes(self):
        provider = WindowsSystemProvider()
        mock_ctypes = MagicMock()
        mock_ctypes.windll.kernel32.GetTickCount64.return_value = 5000000  # 5000s
        with patch.dict(sys.modules, {"ctypes": mock_ctypes}):
            uptime = provider.get_uptime()
            self.assertEqual(uptime, "5000s")

    def test_windows_system_provider_users_dir(self):
        provider = WindowsSystemProvider()
        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", return_value=["Alice", "Bob", "Public", "Default"]):
                with patch("os.path.isdir", return_value=True):
                    users = provider.get_users()
                    names = [u["name"] for u in users]
                    self.assertIn("Alice", names)
                    self.assertIn("Bob", names)
                    self.assertNotIn("Public", names)
                    self.assertNotIn("Default", names)

    def test_windows_process_provider_list_processes(self):
        provider = WindowsProcessProvider()
        csv_out = b'"System Idle Process","0","Services","0","8 K"\r\n"explorer.exe","1234","Console","1","50,000 K","alice"\r\n'
        with patch("subprocess.check_output", return_value=csv_out):
            procs = provider.list_processes()
            self.assertEqual(len(procs), 2)
            self.assertEqual(procs[0]["pid"], 0)
            self.assertEqual(procs[0]["name"], "System Idle Process")
            self.assertEqual(procs[1]["pid"], 1234)
            self.assertEqual(procs[1]["name"], "explorer.exe")

    def test_windows_process_provider_details(self):
        provider = WindowsProcessProvider()
        csv_out = b'"explorer.exe","1234","Console","1","50,000 K"\r\n'
        with patch("subprocess.check_output", return_value=csv_out):
            details = provider.get_process_details(1234)
            self.assertEqual(details["pid"], 1234)
            self.assertEqual(details["name"], "explorer.exe")
            self.assertEqual(details["executable"], "explorer.exe")

    def test_windows_network_provider_routes_route_print(self):
        provider = WindowsNetworkProvider()
        route_out = (
            b"===========================================================================\r\n"
            b"Active Routes:\r\n"
            b"Network Destination        Netmask          Gateway       Interface  Metric\r\n"
            b"          0.0.0.0          0.0.0.0      192.168.1.1     192.168.1.50     25\r\n"
            b"        127.0.0.1  255.255.255.255        On-link        127.0.0.1    331\r\n"
            b"Persistent Routes:\r\n"
            b"  None\r\n"
        )
        with patch("subprocess.check_output", return_value=route_out):
            routes = provider.get_routes()
            self.assertEqual(len(routes), 2)
            self.assertEqual(routes[0]["destination"], "0.0.0.0")
            self.assertEqual(routes[0]["gateway"], "192.168.1.1")
            self.assertEqual(routes[0]["interface"], "192.168.1.50")
            self.assertEqual(routes[0]["metric"], 25)

    def test_windows_network_provider_dns_ipconfig(self):
        provider = WindowsNetworkProvider()
        ipconfig_out = (
            b"Windows IP Configuration\r\n"
            b"   Primary Dns Suffix  . . . . . . . : corp.local\r\n"
            b"   DNS Servers . . . . . . . . . . . : 10.0.0.1\r\n"
            b"                                       10.0.0.2\r\n"
        )
        with patch("subprocess.check_output", return_value=ipconfig_out):
            dns = provider.get_dns()
            self.assertEqual(dns["dns_servers"], ["10.0.0.1", "10.0.0.2"])
            self.assertEqual(dns["search_domains"], ["corp.local"])
            self.assertEqual(dns["configuration"]["source"], "ipconfig")


if __name__ == "__main__":
    unittest.main()
