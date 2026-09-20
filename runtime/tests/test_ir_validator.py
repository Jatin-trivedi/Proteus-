"""
Tests for agent-side IR Validator (Phase 5).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest

from runtime.agent.ir_validator import validate_ir, AgentIRValidationError, APPROVED_OPERATIONS


# ── Helpers ──────────────────────────────────────────────────────────────────

def _valid_ir(ops=None):
    """Returns a minimal valid IR document."""
    if ops is None:
        ops = [{"id": "op-001", "type": "system.info", "parameters": {}}]
    return {
        "version": "1.0",
        "ir_type": "jocky_forensic_ir",
        "investigation": "Test Investigation",
        "operations": ops,
    }


# ── Passing Cases ─────────────────────────────────────────────────────────────

class TestIRValidatorPass:
    def test_valid_minimal_ir(self):
        """Single valid operation passes."""
        validate_ir(_valid_ir())

    def test_valid_multiple_operations(self):
        """Multiple unique operations pass."""
        ops = [
            {"id": "op-001", "type": "system.info", "parameters": {}},
            {"id": "op-002", "type": "network.connections", "parameters": {}},
            {"id": "op-003", "type": "filesystem.hash", "parameters": {"path": "file.txt"}},
        ]
        validate_ir(_valid_ir(ops))

    def test_all_approved_operations_accepted(self):
        """All 10 approved operations are individually accepted."""
        for i, op_type in enumerate(sorted(APPROVED_OPERATIONS)):
            ops = [{"id": f"op-{i:03d}", "type": op_type, "parameters": {}}]
            validate_ir(_valid_ir(ops))

    def test_parameters_none_accepted(self):
        """Operation without parameters key is accepted."""
        ops = [{"id": "op-001", "type": "system.info"}]
        validate_ir(_valid_ir(ops))

    def test_parameters_with_valid_values(self):
        """Parameters with scalar values pass."""
        ops = [{
            "id": "op-001",
            "type": "filesystem.hash",
            "parameters": {"path": "sample.txt", "algorithm": "sha256"},
        }]
        validate_ir(_valid_ir(ops))


# ── Failing Cases ─────────────────────────────────────────────────────────────

class TestIRValidatorFail:
    def test_non_dict_ir_rejected(self):
        with pytest.raises(AgentIRValidationError, match="JSON object"):
            validate_ir("network.connections();")

    def test_list_ir_rejected(self):
        with pytest.raises(AgentIRValidationError):
            validate_ir([{"id": "op-001", "type": "system.info"}])

    def test_missing_version_rejected(self):
        ir = _valid_ir()
        del ir["version"]
        with pytest.raises(AgentIRValidationError, match="version"):
            validate_ir(ir)

    def test_unsupported_version_rejected(self):
        ir = _valid_ir()
        ir["version"] = "99.0"
        with pytest.raises(AgentIRValidationError, match="Unsupported IR version"):
            validate_ir(ir)

    def test_missing_investigation_rejected(self):
        ir = _valid_ir()
        del ir["investigation"]
        with pytest.raises(AgentIRValidationError, match="investigation"):
            validate_ir(ir)

    def test_empty_investigation_rejected(self):
        ir = _valid_ir()
        ir["investigation"] = "   "
        with pytest.raises(AgentIRValidationError, match="investigation"):
            validate_ir(ir)

    def test_missing_operations_rejected(self):
        ir = _valid_ir()
        del ir["operations"]
        with pytest.raises(AgentIRValidationError, match="operations"):
            validate_ir(ir)

    def test_empty_operations_list_rejected(self):
        ir = _valid_ir(ops=[])
        with pytest.raises(AgentIRValidationError, match="at least one"):
            validate_ir(ir)

    def test_non_list_operations_rejected(self):
        ir = _valid_ir()
        ir["operations"] = {"id": "op-001"}
        with pytest.raises(AgentIRValidationError, match="list"):
            validate_ir(ir)

    def test_operation_missing_id_rejected(self):
        ops = [{"type": "system.info", "parameters": {}}]
        with pytest.raises(AgentIRValidationError, match="'id'"):
            validate_ir(_valid_ir(ops))

    def test_duplicate_operation_ids_rejected(self):
        ops = [
            {"id": "op-001", "type": "system.info", "parameters": {}},
            {"id": "op-001", "type": "network.connections", "parameters": {}},
        ]
        with pytest.raises(AgentIRValidationError, match="Duplicate"):
            validate_ir(_valid_ir(ops))

    def test_operation_missing_type_rejected(self):
        ops = [{"id": "op-001", "parameters": {}}]
        with pytest.raises(AgentIRValidationError, match="'type'"):
            validate_ir(_valid_ir(ops))

    def test_unknown_operation_type_rejected(self):
        ops = [{"id": "op-001", "type": "arbitrary.command", "parameters": {}}]
        with pytest.raises(AgentIRValidationError, match="unapproved"):
            validate_ir(_valid_ir(ops))

    def test_os_exec_operation_rejected(self):
        ops = [{"id": "op-001", "type": "os.execute", "parameters": {}}]
        with pytest.raises(AgentIRValidationError, match="unapproved"):
            validate_ir(_valid_ir(ops))

    def test_forbidden_field_code_rejected(self):
        ops = [{"id": "op-001", "type": "system.info", "code": "import os; os.system('ls')"}]
        with pytest.raises(AgentIRValidationError, match="forbidden"):
            validate_ir(_valid_ir(ops))

    def test_forbidden_field_shell_rejected(self):
        ops = [{"id": "op-001", "type": "system.info", "shell": "rm -rf /"}]
        with pytest.raises(AgentIRValidationError, match="forbidden"):
            validate_ir(_valid_ir(ops))

    def test_forbidden_field_exec_rejected(self):
        ops = [{"id": "op-001", "type": "system.info", "exec": "whoami"}]
        with pytest.raises(AgentIRValidationError, match="forbidden"):
            validate_ir(_valid_ir(ops))

    def test_non_dict_parameters_rejected(self):
        ops = [{"id": "op-001", "type": "system.info", "parameters": ["ls", "-la"]}]
        with pytest.raises(AgentIRValidationError, match="parameters"):
            validate_ir(_valid_ir(ops))
