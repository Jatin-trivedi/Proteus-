"""
Proteus JOCKY Forensic Runtime — Forensic Providers Package

Exports base provider interfaces and factory functions to retrieve the
appropriate platform provider instances at runtime.
"""

import platform
from typing import Any, Dict, List, Optional

from runtime.providers.base_provider import (
    FilesystemProvider,
    NetworkProvider,
    ProcessProvider,
    SystemProvider,
)
from runtime.providers.linux import (
    LinuxNetworkProvider,
    LinuxProcessProvider,
    LinuxSystemProvider,
)
from runtime.providers.psutil_provider import (
    PsutilNetworkProvider,
    PsutilProcessProvider,
)
from runtime.providers.windows import (
    WindowsNetworkProvider,
    WindowsProcessProvider,
    WindowsSystemProvider,
)


class CompositeProcessProvider(ProcessProvider):
    """
    Composite process provider that uses psutil when available,
    falling back to native OS CLI tools (tasklist / ps).
    """

    def __init__(self, fallback_provider: ProcessProvider):
        self.psutil_provider = PsutilProcessProvider()
        self.fallback_provider = fallback_provider

    def list_processes(self) -> List[Dict[str, Any]]:
        if self.psutil_provider.is_available:
            try:
                return self.psutil_provider.list_processes()
            except Exception:
                pass
        return self.fallback_provider.list_processes()

    def get_process_details(self, pid: int) -> Dict[str, Any]:
        if self.psutil_provider.is_available:
            try:
                return self.psutil_provider.get_process_details(pid)
            except Exception:
                pass
        return self.fallback_provider.get_process_details(pid)


class CompositeNetworkProvider(NetworkProvider):
    """
    Composite network provider that uses psutil for interfaces/connections
    when available, falling back to OS CLI tools, and uses native OS tools
    for routing tables and DNS configuration.
    """

    def __init__(self, native_provider: NetworkProvider):
        self.psutil_provider = PsutilNetworkProvider()
        self.native_provider = native_provider

    def get_interfaces(self) -> List[Dict[str, Any]]:
        if self.psutil_provider.is_available:
            try:
                return self.psutil_provider.get_interfaces()
            except Exception:
                pass
        return self.native_provider.get_interfaces()

    def get_connections(self) -> List[Dict[str, Any]]:
        if self.psutil_provider.is_available:
            try:
                return self.psutil_provider.get_connections()
            except Exception:
                pass
        return self.native_provider.get_connections()

    def get_routes(self) -> List[Dict[str, Any]]:
        return self.native_provider.get_routes()

    def get_dns(self) -> Dict[str, Any]:
        return self.native_provider.get_dns()


def get_default_system_provider() -> SystemProvider:
    """Factory to instantiate the system provider for the host platform."""
    if platform.system() == "Windows":
        return WindowsSystemProvider()
    return LinuxSystemProvider()


def get_default_process_provider() -> ProcessProvider:
    """Factory to instantiate the process provider for the host platform."""
    if platform.system() == "Windows":
        return CompositeProcessProvider(WindowsProcessProvider())
    return CompositeProcessProvider(LinuxProcessProvider())


def get_default_network_provider() -> NetworkProvider:
    """Factory to instantiate the network provider for the host platform."""
    if platform.system() == "Windows":
        return CompositeNetworkProvider(WindowsNetworkProvider())
    return CompositeNetworkProvider(LinuxNetworkProvider())


__all__ = [
    "SystemProvider",
    "ProcessProvider",
    "NetworkProvider",
    "FilesystemProvider",
    "LinuxSystemProvider",
    "LinuxProcessProvider",
    "LinuxNetworkProvider",
    "WindowsSystemProvider",
    "WindowsProcessProvider",
    "WindowsNetworkProvider",
    "PsutilProcessProvider",
    "PsutilNetworkProvider",
    "CompositeProcessProvider",
    "CompositeNetworkProvider",
    "get_default_system_provider",
    "get_default_process_provider",
    "get_default_network_provider",
]
