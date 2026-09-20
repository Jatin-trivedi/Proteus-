"""
Forensic Intermediate Representation (IR) Data Models for JOCKY.
Defines IRDocument and IROperation models for the contract between the compiler and execution agents.
"""
from dataclasses import dataclass, field
import json
import re
from typing import Any, Dict, List, Optional


class IRValidationError(ValueError):
    """Raised when an IR model fails structural or semantic validation."""
    pass


@dataclass
class IROperation:
    """
    Represents an atomic forensic operation in the JOCKY IR.
    """
    id: str
    type: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not isinstance(self.id, str) or not self.id.strip():
            raise IRValidationError("Operation 'id' must be a non-empty string (e.g. 'op-001').")

        if not isinstance(self.type, str) or not self.type.strip():
            raise IRValidationError("Operation 'type' must be a non-empty string (e.g. 'network.connections').")

        if not isinstance(self.parameters, dict):
            raise IRValidationError(f"Operation 'parameters' must be a dict, got {type(self.parameters).__name__}.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "parameters": dict(self.parameters),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IROperation":
        if not isinstance(data, dict):
            raise IRValidationError(f"Expected dict for IROperation, got {type(data).__name__}.")

        if "id" not in data:
            raise IRValidationError("Missing required field 'id' in IROperation data.")
        if "type" not in data:
            raise IRValidationError("Missing required field 'type' in IROperation data.")

        parameters = data.get("parameters", {})
        if parameters is None:
            parameters = {}

        return cls(
            id=data["id"],
            type=data["type"],
            parameters=parameters,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "IROperation":
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise IRValidationError(f"Invalid JSON string: {e}")
        return cls.from_dict(data)


@dataclass
class IRDocument:
    """
    Represents a complete forensic investigation IR document.
    """
    investigation: str
    operations: List[IROperation] = field(default_factory=list)
    version: str = "1.0"
    ir_type: str = "jocky_forensic_ir"

    def __post_init__(self):
        # Convert any dicts in operations to IROperation objects
        coerced_ops = []
        for op in self.operations:
            if isinstance(op, dict):
                coerced_ops.append(IROperation.from_dict(op))
            elif isinstance(op, IROperation):
                coerced_ops.append(op)
            else:
                raise IRValidationError(f"Invalid operation element of type {type(op).__name__}.")
        self.operations = coerced_ops
        self.validate()

    def validate(self):
        if not isinstance(self.version, str) or not self.version.strip():
            raise IRValidationError("Document 'version' must be a non-empty string.")

        if not isinstance(self.ir_type, str) or not self.ir_type.strip():
            raise IRValidationError("Document 'ir_type' must be a non-empty string.")

        if not isinstance(self.investigation, str) or not self.investigation.strip():
            raise IRValidationError("Document 'investigation' must be a non-empty string.")

        if not isinstance(self.operations, list):
            raise IRValidationError("Document 'operations' must be a list of IROperation objects.")

        for op in self.operations:
            if not isinstance(op, IROperation):
                raise IRValidationError(f"Expected IROperation object in operations list, got {type(op).__name__}.")
            op.validate()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "ir_type": self.ir_type,
            "investigation": self.investigation,
            "operations": [op.to_dict() for op in self.operations],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IRDocument":
        if not isinstance(data, dict):
            raise IRValidationError(f"Expected dict for IRDocument, got {type(data).__name__}.")

        required_fields = ["version", "ir_type", "investigation", "operations"]
        for rf in required_fields:
            if rf not in data:
                raise IRValidationError(f"Missing required field '{rf}' in IRDocument data.")

        raw_ops = data.get("operations", [])
        if not isinstance(raw_ops, list):
            raise IRValidationError("Field 'operations' must be a list.")

        operations = [IROperation.from_dict(op) for op in raw_ops]

        return cls(
            version=data["version"],
            ir_type=data["ir_type"],
            investigation=data["investigation"],
            operations=operations,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "IRDocument":
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise IRValidationError(f"Invalid JSON string: {e}")
        return cls.from_dict(data)

    def to_file(self, filepath: str, indent: int = 2) -> None:
        """Serializes the IRDocument to a JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=indent))

    @classmethod
    def from_file(cls, filepath: str) -> "IRDocument":
        """Deserializes an IRDocument from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return cls.from_json(content)


# ==============================================================================
# Legacy IR Models preserved for intermediate compatibility
# ==============================================================================

@dataclass
class ForensicIROperation:
    id: int
    namespace: str
    function: str
    arguments: List[Any] = field(default_factory=list)
    category: str = "general"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "namespace": self.namespace,
            "function": self.function,
            "arguments": list(self.arguments),
            "category": self.category,
        }


@dataclass
class ForensicIRAnalysis:
    name: str
    operations: List[ForensicIROperation] = field(default_factory=list)
    version: str = "1.0"
    type: str = "forensic_analysis"

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "type": self.type,
            "name": self.name,
            "operations": [op.to_dict() for op in self.operations],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class ForensicIRDocument:
    analyses: List[ForensicIRAnalysis] = field(default_factory=list)

    def to_dict(self) -> dict:
        if len(self.analyses) == 1:
            return self.analyses[0].to_dict()
        return {
            "version": "1.0",
            "type": "forensic_bundle",
            "analyses": [a.to_dict() for a in self.analyses],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
