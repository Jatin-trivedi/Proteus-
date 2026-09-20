"""
Proteus JOCKY Forensic Runtime - Operation Registry
"""

from typing import Dict, Optional, List, Set

try:
    from runtime.collector import BaseCollector, PlaceholderCollector
    from runtime.collectors.system import SystemInfoCollector, SystemUsersCollector
    from runtime.collectors.processes import ProcessesListCollector, ProcessesDetailsCollector
    from runtime.collectors.network import (
        NetworkInterfacesCollector,
        NetworkConnectionsCollector,
        NetworkRoutesCollector,
        NetworkDnsCollector,
    )
    from runtime.collectors.filesystem import (
        FilesystemMetadataCollector,
        FilesystemHashCollector,
    )
except ImportError:
    from collector import BaseCollector, PlaceholderCollector
    from collectors.system import SystemInfoCollector, SystemUsersCollector
    from collectors.processes import ProcessesListCollector, ProcessesDetailsCollector
    from collectors.network import (
        NetworkInterfacesCollector,
        NetworkConnectionsCollector,
        NetworkRoutesCollector,
        NetworkDnsCollector,
    )
    from collectors.filesystem import (
        FilesystemMetadataCollector,
        FilesystemHashCollector,
    )


# Explicit Allowlist of 10 Approved Forensic MVP Operations
APPROVED_OPERATIONS: Set[str] = {
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


class OperationRegistry:
    """
    Registry that maps approved JOCKY forensic operation types to their collector implementations.
    Strictly enforces allowlisted operations to prevent arbitrary execution.
    """

    def __init__(self):
        self._collectors: Dict[str, BaseCollector] = {}

    def register(self, operation_type: str, collector: BaseCollector) -> None:
        """Register a collector for an approved operation type."""
        if not self.is_approved(operation_type):
            raise ValueError(f"Cannot register unapproved operation type: '{operation_type}'")
        if not isinstance(collector, BaseCollector):
            raise TypeError(f"Collector must implement BaseCollector interface, got {type(collector)}")
        self._collectors[operation_type] = collector

    def get(self, operation_type: str) -> Optional[BaseCollector]:
        """Look up a collector by operation type."""
        return self._collectors.get(operation_type)

    def is_registered(self, operation_type: str) -> bool:
        """Check if an operation is currently registered with a collector."""
        return operation_type in self._collectors

    @staticmethod
    def is_approved(operation_type: str) -> bool:
        """Check if an operation type is within the approved allowlist."""
        return operation_type in APPROVED_OPERATIONS

    def list_operations(self) -> List[str]:
        """List all currently registered operation types in sorted order."""
        return sorted(self._collectors.keys())


def create_default_registry() -> OperationRegistry:
    """
    Creates and returns an OperationRegistry pre-populated with actual implementations
    for all 10 approved forensic operations.
    """
    registry = OperationRegistry()
    # System collectors
    registry.register("system.info", SystemInfoCollector())
    registry.register("system.users", SystemUsersCollector())

    # Process collectors
    registry.register("processes.list", ProcessesListCollector())
    registry.register("processes.details", ProcessesDetailsCollector())

    # Network collectors
    registry.register("network.interfaces", NetworkInterfacesCollector())
    registry.register("network.connections", NetworkConnectionsCollector())
    registry.register("network.routes", NetworkRoutesCollector())
    registry.register("network.dns", NetworkDnsCollector())

    # Filesystem collectors
    registry.register("filesystem.metadata", FilesystemMetadataCollector())
    registry.register("filesystem.hash", FilesystemHashCollector())

    # Fallback placeholder check for any remaining approved operations
    for op_type in sorted(APPROVED_OPERATIONS):
        if not registry.is_registered(op_type):
            registry.register(op_type, PlaceholderCollector(op_type))

    return registry




