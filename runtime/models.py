"""
Proteus JOCKY Forensic Runtime - Result Data Models
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union

try:
    from runtime.errors import StructuredError
except ImportError:
    from errors import StructuredError


@dataclass
class OperationResult:
    """Represents the execution result of a single forensic IR operation."""
    operation_id: str
    type: str
    status: str  # "success" or "error"
    data: Optional[Dict[str, Any]] = None
    error: Optional[Union[StructuredError, Dict[str, str]]] = None
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        err_dict = None
        if isinstance(self.error, StructuredError):
            err_dict = self.error.to_dict()
        elif isinstance(self.error, dict):
            err_dict = self.error

        res = {
            "operation_id": self.operation_id,
            "type": self.type,
            "status": self.status,
            "data": self.data if self.status == "success" else None,
            "error": err_dict if self.status == "error" else None,
        }
        return res


    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class ExecutionResult:
    """Represents the complete execution result of a JOCKY IR Document."""
    investigation: str
    version: str
    results: List[OperationResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation": self.investigation,
            "version": self.version,
            "results": [r.to_dict() for r in self.results]
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
