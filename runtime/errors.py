"""
Proteus JOCKY Forensic Runtime - Errors and Exception Definitions
"""

from typing import Dict, Any


class ErrorCode:
    UNKNOWN_OPERATION = "UNKNOWN_OPERATION"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    COLLECTION_FAILED = "COLLECTION_FAILED"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    PERMISSION_DENIED = "PERMISSION_DENIED"


class StructuredError:
    """Standard structured error representation for runtime operations."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

    def to_dict(self) -> Dict[str, str]:
        return {
            "code": self.code,
            "message": self.message
        }

    def __repr__(self) -> str:
        return f"StructuredError(code={self.code!r}, message={self.message!r})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, StructuredError):
            return self.code == other.code and self.message == other.message
        if isinstance(other, dict):
            return self.to_dict() == other
        return False


class CollectorException(Exception):
    """Exception raised by forensic collectors when an operation fails."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_structured_error(self) -> StructuredError:
        return StructuredError(code=self.code, message=self.message)
