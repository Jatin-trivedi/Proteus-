"""
Proteus JOCKY Forensic Runtime - System Collectors
Implements:
- system.info()
- system.users()

Delegates platform-specific data acquisition to ForensicProvider.
"""

from typing import Any, Dict, List, Optional

try:
    from runtime.collector import BaseCollector
    from runtime.errors import CollectorException, ErrorCode
    from runtime.providers import SystemProvider, get_default_system_provider
except ImportError:
    from collector import BaseCollector
    from errors import CollectorException, ErrorCode
    from providers import SystemProvider, get_default_system_provider


def _get_uptime_string() -> str:
    """Calculates system uptime in a cross-platform and graceful manner."""
    return get_default_system_provider().get_uptime()


def _get_current_username() -> str:
    """Retrieves current user name cross-platform."""
    return get_default_system_provider().get_username()


class SystemInfoCollector(BaseCollector):
    """
    Forensic collector for 'system.info'.
    Collects hostname, OS, architecture, kernel version, uptime, and current username.
    """

    def __init__(self, provider: Optional[SystemProvider] = None):
        self.provider = provider or get_default_system_provider()

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        hostname = self.provider.get_hostname()
        os_name = self.provider.get_os()
        architecture = self.provider.get_architecture()
        kernel = self.provider.get_kernel()
        uptime = self.provider.get_uptime()
        username = self.provider.get_username()

        return {
            "hostname": str(hostname),
            "os": str(os_name),
            "architecture": str(architecture),
            "kernel": str(kernel),
            "uptime": str(uptime),
            "username": str(username),
        }


class SystemUsersCollector(BaseCollector):
    """
    Forensic collector for 'system.users'.
    Safely and read-only enumerates local users on the endpoint.
    Handles permission or platform errors gracefully.
    """

    def __init__(self, provider: Optional[SystemProvider] = None):
        self.provider = provider or get_default_system_provider()

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        users = self.provider.get_users()
        return {
            "users": users
        }
