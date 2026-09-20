"""
Proteus JOCKY Forensic Runtime Package
"""

try:
    from runtime.errors import StructuredError, ErrorCode, CollectorException
    from runtime.models import OperationResult, ExecutionResult
    from runtime.collector import BaseCollector, PlaceholderCollector
    from runtime.registry import OperationRegistry, create_default_registry, APPROVED_OPERATIONS
    from runtime.dispatcher import OperationDispatcher
except ImportError:
    from errors import StructuredError, ErrorCode, CollectorException
    from models import OperationResult, ExecutionResult
    from collector import BaseCollector, PlaceholderCollector
    from registry import OperationRegistry, create_default_registry, APPROVED_OPERATIONS
    from dispatcher import OperationDispatcher

__all__ = [
    "StructuredError",
    "ErrorCode",
    "CollectorException",
    "OperationResult",
    "ExecutionResult",
    "BaseCollector",
    "PlaceholderCollector",
    "OperationRegistry",
    "create_default_registry",
    "APPROVED_OPERATIONS",
    "OperationDispatcher",
]
