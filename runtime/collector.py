"""
Proteus JOCKY Forensic Runtime - Collector Interface and Protocol
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

try:
    from runtime.errors import CollectorException, ErrorCode
except ImportError:
    from errors import CollectorException, ErrorCode


class BaseCollector(ABC):
    """Abstract base class for all approved forensic collectors."""

    @abstractmethod
    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the forensic collection operation and return structured data.
        
        :param parameters: Key-value dictionary of arguments passed in the IR.
        :return: Structured result dictionary.
        :raises CollectorException: When collection fails.
        """
        pass


class PlaceholderCollector(BaseCollector):
    """
    Placeholder collector used when a collector implementation is not yet provided.
    Always raises a structured CollectorException with NOT_IMPLEMENTED error code.
    """

    def __init__(self, operation_type: str):
        self.operation_type = operation_type

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        raise CollectorException(
            code=ErrorCode.NOT_IMPLEMENTED,
            message=f"Collector for '{self.operation_type}' is not yet implemented"
        )
