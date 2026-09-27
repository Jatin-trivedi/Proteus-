"""
Central Forensic Function Registry for JOCKY.
Defines all approved forensic collectors, their signatures, and domain categories.
This registry is reusable by the Proteus agent runtime.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ArgumentSpec:
    name: str
    type: str  # 'string', 'number', 'boolean'
    description: str = ""
    optional: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "optional": self.optional,
        }


@dataclass
class FunctionSpec:
    namespace: str
    name: str
    description: str
    category: str
    arguments: List[ArgumentSpec] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.namespace}.{self.name}"

    @property
    def min_args(self) -> int:
        return len([a for a in self.arguments if not a.optional])

    @property
    def max_args(self) -> int:
        return len(self.arguments)

    def to_dict(self) -> dict:
        return {
            "namespace": self.namespace,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "arguments": [arg.to_dict() for arg in self.arguments],
        }


class ForensicFunctionRegistry:
    def __init__(self):
        self._namespaces: Dict[str, Dict[str, FunctionSpec]] = {}
        self._initialize_default_registry()

    def _initialize_default_registry(self):
        # 1. system namespace
        self.register(
            FunctionSpec(
                namespace="system",
                name="info",
                category="system",
                description="Collects core host metadata (OS, hostname, architecture, uptime, kernel version).",
                arguments=[],
            )
        )
        self.register(
            FunctionSpec(
                namespace="system",
                name="users",
                category="system",
                description="Enumerates local user accounts, active sessions, and privilege levels.",
                arguments=[],
            )
        )

        # 2. processes namespace
        self.register(
            FunctionSpec(
                namespace="processes",
                name="list",
                category="process",
                description="Lists all running processes with PID, PPID, executable path, username, and memory usage.",
                arguments=[],
            )
        )
        self.register(
            FunctionSpec(
                namespace="processes",
                name="details",
                category="process",
                description="Collects detailed forensic process information (threads, handles, loaded DLLs/modules, environment variables).",
                arguments=[
                    ArgumentSpec(name="pid", type="number", description="Process Identifier (PID) to inspect"),
                ],
            )
        )

        # 3. network namespace
        self.register(
            FunctionSpec(
                namespace="network",
                name="interfaces",
                category="network",
                description="Enumerates network adapters, MAC addresses, IPv4/IPv6 addresses, and adapter status.",
                arguments=[],
            )
        )
        self.register(
            FunctionSpec(
                namespace="network",
                name="connections",
                category="network",
                description="Collects active TCP/UDP network connections, listening sockets, and associated PIDs.",
                arguments=[],
            )
        )
        self.register(
            FunctionSpec(
                namespace="network",
                name="routes",
                category="network",
                description="Dumps the system IP routing table and gateway configurations.",
                arguments=[],
            )
        )
        self.register(
            FunctionSpec(
                namespace="network",
                name="dns",
                category="network",
                description="Extracts local DNS cache, resolver configuration, and DNS query history.",
                arguments=[],
            )
        )

        # 4. filesystem namespace
        self.register(
            FunctionSpec(
                namespace="filesystem",
                name="metadata",
                category="filesystem",
                description="Gathers filesystem metadata (timestamps MACB, permissions, owner, size) for a given path.",
                arguments=[
                    ArgumentSpec(name="path", type="string", description="File or directory path to inspect"),
                ],
            )
        )
        self.register(
            FunctionSpec(
                namespace="filesystem",
                name="hash",
                category="filesystem",
                description="Computes cryptographic hashes (SHA-256, MD5) for the target file or directory.",
                arguments=[
                    ArgumentSpec(name="path", type="string", description="Target file path to calculate hashes for"),
                ],
            )
        )

    def register(self, spec: FunctionSpec):
        if spec.namespace not in self._namespaces:
            self._namespaces[spec.namespace] = {}
        self._namespaces[spec.namespace][spec.name] = spec

    def has_namespace(self, namespace: str) -> bool:
        return namespace in self._namespaces

    def has_function(self, namespace: str, function: str) -> bool:
        return namespace in self._namespaces and function in self._namespaces[namespace]

    def get_function_spec(self, namespace: str, function: str) -> Optional[FunctionSpec]:
        if self.has_function(namespace, function):
            return self._namespaces[namespace][function]
        return None

    def get_available_functions(self, namespace: str) -> List[str]:
        if namespace in self._namespaces:
            return sorted(list(self._namespaces[namespace].keys()))
        return []

    def get_all_namespaces(self) -> List[str]:
        return sorted(list(self._namespaces.keys()))

    def to_dict(self) -> dict:
        result = {}
        for ns, funcs in self._namespaces.items():
            result[ns] = {fname: fspec.to_dict() for fname, fspec in funcs.items()}
        return result


# Global default registry instance
DEFAULT_REGISTRY = ForensicFunctionRegistry()
