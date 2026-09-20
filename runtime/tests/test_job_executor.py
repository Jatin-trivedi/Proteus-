"""
Tests for JobExecutor (Phase 6).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest

from runtime.agent.job_executor import JobExecutor, DEFAULT_JOB_TIMEOUT_SEC


VALID_IR = {
    "version": "1.0",
    "ir_type": "jocky_forensic_ir",
    "investigation": "Test Investigation",
    "operations": [
        {"id": "op-001", "type": "system.info", "parameters": {}},
    ],
}

MULTI_OP_IR = {
    "version": "1.0",
    "ir_type": "jocky_forensic_ir",
    "investigation": "Multi-Op",
    "operations": [
        {"id": "op-001", "type": "system.info", "parameters": {}},
        {"id": "op-002", "type": "processes.list", "parameters": {}},
    ],
}

INVALID_IR = {
    "version": "1.0",
    "ir_type": "jocky_forensic_ir",
    "investigation": "Bad",
    "operations": [
        {"id": "op-001", "type": "evil.command", "parameters": {}},
    ],
}

FORBIDDEN_IR = {
    "version": "1.0",
    "investigation": "Forbidden",
    "operations": [
        {"id": "op-001", "type": "system.info", "shell": "rm -rf /"},
    ],
}


class TestJobExecutor:
    def setup_method(self):
        self.executor = JobExecutor(agent_id="agent-test-001", timeout_sec=60)

    def test_valid_ir_executes(self):
        """Valid IR with approved operation executes and returns completed status."""
        result = self.executor.execute_job(
            job_id="JOB-TEST-001",
            investigation_id="INV-001",
            ir=VALID_IR,
        )
        assert result["status"] == "completed"
        assert result["agent_id"] == "agent-test-001"
        assert isinstance(result["results"], list)
        assert len(result["results"]) > 0

    def test_multiple_operations_execute(self):
        """Multiple operations all execute."""
        result = self.executor.execute_job(
            job_id="JOB-TEST-002",
            investigation_id="INV-001",
            ir=MULTI_OP_IR,
        )
        assert result["status"] == "completed"
        assert len(result["results"]) == 2

    def test_invalid_operation_type_rejected(self):
        """IR with unapproved operation type is rejected before dispatch."""
        result = self.executor.execute_job(
            job_id="JOB-TEST-003",
            investigation_id="INV-001",
            ir=INVALID_IR,
        )
        assert result["status"] == "failed"
        assert "IR_VALIDATION_FAILED" in result["error"]

    def test_forbidden_field_rejected(self):
        """IR with forbidden fields is rejected."""
        result = self.executor.execute_job(
            job_id="JOB-TEST-004",
            investigation_id="INV-001",
            ir=FORBIDDEN_IR,
        )
        assert result["status"] == "failed"

    def test_evidence_generated_per_operation(self):
        """Each operation generates one evidence item."""
        result = self.executor.execute_job(
            job_id="JOB-TEST-005",
            investigation_id="INV-001",
            ir=MULTI_OP_IR,
        )
        assert len(result["evidence"]) == 2
        for item in result["evidence"]:
            assert "evidence_id" in item
            assert "sha256" in item
            assert len(item["sha256"]) == 64

    def test_evidence_sha256_non_empty(self):
        """Evidence SHA-256 hashes are non-empty hex strings."""
        result = self.executor.execute_job(
            job_id="JOB-TEST-006",
            investigation_id="INV-001",
            ir=VALID_IR,
        )
        assert result["status"] == "completed"
        evidence = result["evidence"]
        assert len(evidence) >= 1
        sha = evidence[0]["sha256"]
        assert len(sha) == 64
        assert all(c in "0123456789abcdef" for c in sha)

    def test_integrity_hash_present(self):
        """Result includes package-level integrity hash."""
        result = self.executor.execute_job(
            job_id="JOB-TEST-007",
            investigation_id="INV-001",
            ir=VALID_IR,
        )
        assert "integrity" in result
        assert result["integrity"]["algorithm"] == "SHA-256"

    def test_timestamps_present(self):
        """Result contains started_at and completed_at."""
        result = self.executor.execute_job(
            job_id="JOB-TEST-008",
            investigation_id="INV-001",
            ir=VALID_IR,
        )
        assert "started_at" in result
        assert "completed_at" in result

    def test_failure_result_structure(self):
        """Failure result has correct structure."""
        result = self.executor.execute_job(
            job_id="JOB-TEST-009",
            investigation_id="INV-001",
            ir=INVALID_IR,
        )
        assert result["status"] == "failed"
        assert "error" in result
        assert "started_at" in result
        assert "completed_at" in result
        assert result["evidence"] == []
