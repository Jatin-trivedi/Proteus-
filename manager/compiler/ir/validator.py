"""
JOCKY IR Validation and Schema Enforcement Subsystem.
Provides comprehensive validation of JOCKY IR documents against the schema and forensic registry.
"""
from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Optional, Union

try:
    from compiler.ir.model import IRDocument, IROperation, IRValidationError
    from compiler.semantic.registry import ForensicFunctionRegistry, DEFAULT_REGISTRY
except (ImportError, ModuleNotFoundError):
    from ir.model import IRDocument, IROperation, IRValidationError
    from semantic.registry import ForensicFunctionRegistry, DEFAULT_REGISTRY

SUPPORTED_VERSIONS = {"1.0"}
EXPECTED_IR_TYPE = "jocky_forensic_ir"


@dataclass
class ValidationResult:
    """
    Result of an IR validation check containing success status and structured errors.
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    document: Optional[IRDocument] = None

    def __bool__(self) -> bool:
        return self.is_valid

    def format_errors(self) -> str:
        if not self.errors:
            return "No validation errors."
        return "\n".join(f"- {err}" for err in self.errors)


class IRValidator:
    def __init__(self, registry: Optional[ForensicFunctionRegistry] = None):
        self.registry = registry or DEFAULT_REGISTRY

    def validate(
        self,
        target: Union[IRDocument, Dict[str, Any], str],
        strict_registry: bool = True,
    ) -> ValidationResult:
        """
        Validates an IRDocument instance, raw dict, or JSON string.
        Returns a structured ValidationResult.
        """
        errors: List[str] = []
        raw_data: Optional[Dict[str, Any]] = None
        doc: Optional[IRDocument] = None

        # 1. Parse JSON string if needed
        if isinstance(target, str):
            try:
                raw_data = json.loads(target)
            except json.JSONDecodeError as e:
                return ValidationResult(is_valid=False, errors=[f"Invalid JSON syntax: {e}"])
        elif isinstance(target, dict):
            raw_data = target
        elif isinstance(target, IRDocument):
            doc = target
            raw_data = target.to_dict()
        else:
            return ValidationResult(
                is_valid=False,
                errors=[f"Expected IRDocument, dict, or JSON string, got {type(target).__name__}"],
            )

        # 2. Validate Document Header Fields
        if not isinstance(raw_data, dict):
            return ValidationResult(is_valid=False, errors=["Root IR must be a JSON object / dict."])

        # Version check
        if "version" not in raw_data:
            errors.append("Missing required field 'version'.")
        elif not isinstance(raw_data["version"], str):
            errors.append("Field 'version' must be a string.")
        elif raw_data["version"] not in SUPPORTED_VERSIONS:
            errors.append(
                f"Unsupported IR version '{raw_data['version']}'. Supported versions: {sorted(list(SUPPORTED_VERSIONS))}."
            )

        # ir_type check
        if "ir_type" not in raw_data:
            errors.append("Missing required field 'ir_type'.")
        elif raw_data["ir_type"] != EXPECTED_IR_TYPE:
            errors.append(
                f"Invalid 'ir_type' '{raw_data['ir_type']}'. Expected '{EXPECTED_IR_TYPE}'."
            )

        # investigation check
        if "investigation" not in raw_data:
            errors.append("Missing required field 'investigation'.")
        elif not isinstance(raw_data["investigation"], str) or not raw_data["investigation"].strip():
            errors.append("Field 'investigation' must be a non-empty string.")

        # operations list check
        if "operations" not in raw_data:
            errors.append("Missing required field 'operations'.")
        elif not isinstance(raw_data["operations"], list):
            errors.append("Field 'operations' must be an array / list.")

        # If top-level structure is broken, return errors early
        if errors:
            return ValidationResult(is_valid=False, errors=errors)

        # 3. Validate Operations
        seen_ids = set()
        operations_list = raw_data.get("operations", [])

        for idx, raw_op in enumerate(operations_list, start=1):
            op_label = f"Operation #{idx}"

            if not isinstance(raw_op, dict):
                errors.append(f"{op_label}: Must be a JSON object / dict.")
                continue

            # Check ID
            if "id" not in raw_op:
                errors.append(f"{op_label}: Missing required field 'id'.")
                op_id = None
            elif not isinstance(raw_op["id"], str) or not raw_op["id"].strip():
                errors.append(f"{op_label}: Field 'id' must be a non-empty string.")
                op_id = None
            else:
                op_id = raw_op["id"]
                op_label = f"Operation '{op_id}'"
                if op_id in seen_ids:
                    errors.append(f"{op_label}: Duplicate operation ID '{op_id}'.")
                seen_ids.add(op_id)

            # Check type
            op_type = raw_op.get("type")
            if not op_type:
                errors.append(f"{op_label}: Missing required field 'type'.")
            elif not isinstance(op_type, str) or "." not in op_type:
                errors.append(f"{op_label}: Field 'type' must be in format '<namespace>.<function>', got '{op_type}'.")
            elif strict_registry and self.registry:
                parts = op_type.split(".", 1)
                namespace, function = parts[0], parts[1]
                if not self.registry.has_namespace(namespace):
                    errors.append(f"{op_label}: Unknown forensic namespace '{namespace}' in type '{op_type}'.")
                elif not self.registry.has_function(namespace, function):
                    errors.append(f"{op_label}: Unknown forensic function '{function}' in namespace '{namespace}'.")
                else:
                    spec = self.registry.get_function_spec(namespace, function)
                    # Check parameters against registered spec
                    params = raw_op.get("parameters")
                    if params is not None and isinstance(params, dict) and spec:
                        # Check required arguments
                        for arg_spec in spec.arguments:
                            if not arg_spec.optional and arg_spec.name not in params:
                                errors.append(
                                    f"{op_label}: Missing required parameter '{arg_spec.name}' for function '{op_type}'."
                                )
                            elif arg_spec.name in params:
                                val = params[arg_spec.name]
                                if arg_spec.type == "string" and not isinstance(val, str):
                                    errors.append(
                                        f"{op_label}: Parameter '{arg_spec.name}' expects type 'string', got {type(val).__name__}."
                                    )
                                elif arg_spec.type == "number" and not isinstance(val, (int, float)):
                                    errors.append(
                                        f"{op_label}: Parameter '{arg_spec.name}' expects type 'number', got {type(val).__name__}."
                                    )
                                elif arg_spec.type == "boolean" and not isinstance(val, bool):
                                    errors.append(
                                        f"{op_label}: Parameter '{arg_spec.name}' expects type 'boolean', got {type(val).__name__}."
                                    )

                        # Check for unknown extra parameters
                        registered_arg_names = {a.name for a in spec.arguments}
                        for p_name in params:
                            if p_name not in registered_arg_names:
                                errors.append(
                                    f"{op_label}: Unknown parameter '{p_name}' for forensic function '{op_type}'."
                                )

            # Check parameters object
            if "parameters" not in raw_op:
                errors.append(f"{op_label}: Missing required field 'parameters'.")
            elif not isinstance(raw_op["parameters"], dict):
                errors.append(f"{op_label}: Field 'parameters' must be a JSON object / dict.")

        if errors:
            return ValidationResult(is_valid=False, errors=errors)

        # 4. Construct IRDocument if not already built
        if doc is None:
            try:
                doc = IRDocument.from_dict(raw_data)
            except Exception as e:
                return ValidationResult(is_valid=False, errors=[str(e)])

        return ValidationResult(is_valid=True, errors=[], document=doc)


def validate_ir(
    target: Union[IRDocument, Dict[str, Any], str],
    registry: Optional[ForensicFunctionRegistry] = None,
) -> ValidationResult:
    """Convenience functional interface for IR validation."""
    return IRValidator(registry).validate(target)
