"""
Proteus JOCKY Forensic Runtime — ForensicProvider Base Interfaces

Defines abstract base classes (ABCs) for each forensic domain.
Platform adapters (Windows, Linux, psutil, Unix) implement these interfaces.
Collectors delegate to a provider instance, keeping their own code
completely platform-independent.

No platform detection or OS-specific logic lives here.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SystemProvider(ABC):
    """
    Abstract interface for system-level forensic data acquisition.
    Covers: hostname, OS identity, architecture, kernel, uptime, users.
    """

    @abstractmethod
    def get_hostname(self) -> str:
        """Return the machine hostname."""

    @abstractmethod
    def get_os(self) -> str:
        """Return the OS name (e.g. 'Windows', 'Linux', 'Darwin')."""

    @abstractmethod
    def get_architecture(self) -> str:
        """Return the CPU architecture (e.g. 'x86_64', 'arm64')."""

    @abstractmethod
    def get_kernel(self) -> str:
        """Return the OS kernel/release version string."""

    @abstractmethod
    def get_uptime(self) -> str:
        """Return system uptime as a string with trailing 's' (e.g. '12345s')."""

    @abstractmethod
    def get_username(self) -> str:
        """Return the name of the currently active user."""

    @abstractmethod
    def get_users(self) -> List[Dict[str, str]]:
        """
        Return a list of local user account dictionaries.
        Each entry: {"name": str, "type": "local"}
        """


class ProcessProvider(ABC):
    """
    Abstract interface for process forensic data acquisition.
    Covers: process list enumeration and per-PID detail lookup.
    """

    @abstractmethod
    def list_processes(self) -> List[Dict[str, Any]]:
        """
        Return a list of running process dictionaries.
        Each entry: {"pid": int, "name": str, "parent_pid": int, "username": str}
        Raises CollectorException on total failure.
        """

    @abstractmethod
    def get_process_details(self, pid: int) -> Dict[str, Any]:
        """
        Return detailed forensic information for a single process.
        Result: {"pid": int, "name": str, "parent_pid": int,
                 "start_time": str, "executable": str}
        Raises CollectorException(COLLECTION_FAILED) if PID does not exist.
        Raises CollectorException(PERMISSION_DENIED) if access is denied.
        """


class NetworkProvider(ABC):
    """
    Abstract interface for network forensic data acquisition.
    Covers: interfaces, active connections, routing table, DNS configuration.
    """

    @abstractmethod
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """
        Return a list of network interface dictionaries.
        Each entry: {"name": str, "addresses": List[str], "mac": str}
        """

    @abstractmethod
    def get_connections(self) -> List[Dict[str, Any]]:
        """
        Return a list of active socket/connection dictionaries.
        Each entry: {"protocol": str, "local": str, "remote": str,
                     "state": str, "pid": int}
        """

    @abstractmethod
    def get_routes(self) -> List[Dict[str, Any]]:
        """
        Return a list of routing table entry dictionaries.
        Each entry: {"destination": str, "gateway": str,
                     "interface": str, "metric": int}
        """

    @abstractmethod
    def get_dns(self) -> Dict[str, Any]:
        """
        Return DNS resolver configuration.
        Result: {"dns_servers": List[str], "search_domains": List[str],
                 "configuration": dict}
        """


class FilesystemProvider(ABC):
    """
    Abstract interface for filesystem forensic data acquisition.
    Covers: file/directory metadata and cryptographic hashing.
    """

    @abstractmethod
    def get_metadata(self, path: str) -> Dict[str, Any]:
        """
        Return filesystem metadata for a path.
        Result: {"path": str, "size": int, "creation_time": str,
                 "modification_time": str, "access_time": str, "permissions": str}
        Raises CollectorException on missing path or permission failure.
        """

    @abstractmethod
    def get_hash(self, path: str) -> Dict[str, Any]:
        """
        Compute the SHA-256 hash of a file in read-only mode.
        Result: {"path": str, "algorithm": "SHA-256", "hash": str}
        Raises CollectorException on missing path or permission failure.
        """
