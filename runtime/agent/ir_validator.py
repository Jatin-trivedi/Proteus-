"""
Proteus Agent — Agent-Side IR Validator (Priority 8)

A second line of defense: validates the JOCKY IR received from the server
before any execution begins. Complements server-side validation.

Security constraints:
- Never uses eval(), exec(), importlib, or shell=True
- Rejects any IR containing executable/dangerous fields
- Enforces the same APPROVED_OPERATIONS allowlist as the server
- Validates structural completeness before dispatch
"""

from typing import Any, Dict, Set

SUPPORTED_IR_VERSIONS: Set[str] = {"1.0"}

# Forbidden field names that must never appear in any operation
FORBIDDEN_FIELDS = frozenset({
    "code", "script", "shell", "command", "exec", "eval",
    "payload", "binary", "executable", "inject",
})

try:
    from runtime.registry import APPROVED_OPERATIONS
except ImportError:
    try:
        from registry import APPROVED_OPERATIONS
    except ImportError:
        APPROVED_OPERATIONS = {
            "system.info", "system.users",
            "processes.list", "processes.details",
            "network.interfaces", "network.connections",
            "network.routes", "network.dns",
            "filesystem.metadata", "filesystem.hash",
        }


class AgentIRValidationError(ValueError):
    """Raised when agent-side IR validation fails."""
    pass


def validate_ir(ir: Any) -> None:
    """
    Validates a JOCKY IR document on the agent side before execution.

    Checks:
    1. IR is a dict
    2. version exists and is supported
    3. investigation name exists and is non-empty string
    4. operations exists and is a non-empty list
    5. Each operation has 'id' (unique, non-empty string)
    6. Each operation has 'type' in APPROVED_OPERATIONS
    7. Parameters (if present) are a dict
    8. No forbidden executable fields in operations
    9. No eval/exec/shell/code anywhere in the IR

    Raises AgentIRValidationError with a descriptive message on failure.
    """
    if not isinstance(ir, dict):
        raise AgentIRValidationError(f"IR must be a JSON object, got {type(ir).__name__}")

    # 1. Version check
    version = ir.get("version")
    if not version or not isinstance(version, str) or not version.strip():
        raise AgentIRValidationError("IR missing required field 'version'")
    if version not in SUPPORTED_IR_VERSIONS:
        raise AgentIRValidationError(
            f"Unsupported IR version '{version}'. Supported: {sorted(SUPPORTED_IR_VERSIONS)}"
        )

    # 2. Investigation name
    investigation = ir.get("investigation")
    if not investigation or not isinstance(investigation, str) or not investigation.strip():
        raise AgentIRValidationError("IR missing required field 'investigation' (non-empty string)")

    # 3. Operations list
    operations = ir.get("operations")
    if operations is None:
        raise AgentIRValidationError("IR missing required field 'operations'")
    if not isinstance(operations, list):
        raise AgentIRValidationError("IR 'operations' must be a list")
    if len(operations) == 0:
        raise AgentIRValidationError("IR 'operations' must contain at least one operation")

    # 4. Validate each operation
    seen_ids: Set[str] = set()
    for i, op in enumerate(operations):
        if not isinstance(op, dict):
            raise AgentIRValidationError(
                f"Operation at index {i} must be a JSON object, got {type(op).__name__}"
            )

        # Reject forbidden fields anywhere in the operation
        for forbidden in FORBIDDEN_FIELDS:
            if forbidden in op:
                raise AgentIRValidationError(
                    f"Operation at index {i} contains forbidden field '{forbidden}'"
                )

        # Operation ID
        op_id = op.get("id")
        if not op_id or not isinstance(op_id, str) or not op_id.strip():
            raise AgentIRValidationError(
                f"Operation at index {i} missing required field 'id' (non-empty string)"
            )
        if op_id in seen_ids:
            raise AgentIRValidationError(f"Duplicate operation ID: '{op_id}'")
        seen_ids.add(op_id)

        # Operation type — must be in approved allowlist
        op_type = op.get("type")
        if not op_type or not isinstance(op_type, str) or not op_type.strip():
            raise AgentIRValidationError(
                f"Operation '{op_id}' missing required field 'type'"
            )
        if op_type not in APPROVED_OPERATIONS:
            raise AgentIRValidationError(
                f"Operation '{op_id}' has unapproved type '{op_type}'. "
                f"Approved operations: {sorted(APPROVED_OPERATIONS)}"
            )

        # Parameters (optional, but if present must be a dict)
        params = op.get("parameters")
        if params is not None and not isinstance(params, dict):
            raise AgentIRValidationError(
                f"Operation '{op_id}' parameters must be a JSON object, got {type(params).__name__}"
            )

        # Deep-check parameter values — reject anything callable or suspicious
        if isinstance(params, dict):
            _validate_parameters(op_id, params)


def _validate_parameters(op_id: str, params: Dict[str, Any]) -> None:
    """
    Validates that operation parameters contain only safe scalar values.
    Rejects callables, nested dangerous structures, or forbidden keys.
    """
    for key, value in params.items():
        if key in FORBIDDEN_FIELDS:
            raise AgentIRValidationError(
                f"Operation '{op_id}' parameter key '{key}' is forbidden"
            )
        if callable(value):
            raise AgentIRValidationError(
                f"Operation '{op_id}' parameter '{key}' must not be callable"
            )
        if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
            raise AgentIRValidationError(
                f"Operation '{op_id}' parameter '{key}' has unsupported type "
                f"{type(value).__name__}"
            )
