"""
Tests for Evidence generation and SHA-256 integrity (Phase 7).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import pytest

from runtime.agent.evidence import (
    EvidenceItem,
    EvidencePackage,
    compute_sha256,
    _canonical_json,
)


class TestEvidenceIntegrity:
    def test_sha256_deterministic(self):
        """Same data always produces the same hash."""
        data = {"connections": [{"pid": 1, "port": 80}], "count": 1}
        h1 = compute_sha256(data)
        h2 = compute_sha256(data)
        assert h1 == h2

    def test_sha256_canonical_sorted_keys(self):
        """Key order doesn't affect the hash (canonical form)."""
        data1 = {"b": 2, "a": 1}
        data2 = {"a": 1, "b": 2}
        assert compute_sha256(data1) == compute_sha256(data2)

    def test_sha256_different_data_different_hash(self):
        """Different data produces different hashes."""
        h1 = compute_sha256({"key": "value1"})
        h2 = compute_sha256({"key": "value2"})
        assert h1 != h2

    def test_sha256_is_64_char_hex(self):
        """SHA-256 output is always 64 hex characters."""
        h = compute_sha256({"test": True})
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_canonical_json_compact(self):
        """Canonical JSON uses compact form with sorted keys."""
        result = _canonical_json({"z": 1, "a": 2})
        assert result == '{"a":2,"z":1}'


class TestEvidenceItem:
    def test_evidence_item_creation(self):
        """EvidenceItem created from operation result."""
        item = EvidenceItem.from_operation_result(
            job_id="JOB-001",
            agent_id="agent-abc",
            operation_id="op-001",
            operation_type="system.info",
            data={"hostname": "test-host"},
        )
        assert item.job_id == "JOB-001"
        assert item.agent_id == "agent-abc"
        assert item.operation_id == "op-001"
        assert item.operation_type == "system.info"
        assert item.sha256 is not None
        assert len(item.sha256) == 64
        assert item.evidence_id.startswith("EVD-")

    def test_evidence_item_verify(self):
        """Freshly created evidence item passes verification."""
        item = EvidenceItem.from_operation_result(
            job_id="JOB-001",
            agent_id="agent-abc",
            operation_id="op-002",
            operation_type="network.connections",
            data={"connections": []},
        )
        assert item.verify() is True

    def test_evidence_item_tampered_fails_verify(self):
        """Tampered data fails integrity check."""
        item = EvidenceItem.from_operation_result(
            job_id="JOB-001",
            agent_id="agent-abc",
            operation_id="op-003",
            operation_type="system.users",
            data={"users": ["admin"]},
        )
        # Tamper with data after creation
        item.data = {"users": ["admin", "attacker"]}
        assert item.verify() is False

    def test_evidence_item_to_dict_structure(self):
        """to_dict returns all required fields."""
        item = EvidenceItem.from_operation_result(
            job_id="JOB-001",
            agent_id="agent-abc",
            operation_id="op-001",
            operation_type="system.info",
            data={"os": "linux"},
        )
        d = item.to_dict()
        for key in ("evidence_id", "job_id", "agent_id", "operation_id",
                    "operation_type", "collected_at", "data", "sha256", "schema_version"):
            assert key in d


class TestEvidencePackage:
    def test_evidence_package_build(self):
        """EvidencePackage builds with correct structure."""
        item = EvidenceItem.from_operation_result(
            job_id="JOB-001",
            agent_id="agent-abc",
            operation_id="op-001",
            operation_type="system.info",
            data={"hostname": "host1"},
        )
        op_results = [{"operation_id": "op-001", "type": "system.info", "status": "success", "data": {"hostname": "host1"}}]
        package = EvidencePackage.build(
            job_id="JOB-001",
            agent_id="agent-abc",
            investigation_id="INV-001",
            started_at="2026-01-01T00:00:00+00:00",
            completed_at="2026-01-01T00:01:00+00:00",
            status="completed",
            operation_results=op_results,
            evidence_items=[item],
        )
        assert package.job_id == "JOB-001"
        assert package.package_hash is not None
        assert len(package.package_hash) == 64

    def test_evidence_package_to_dict(self):
        """Package dict has expected top-level keys."""
        item = EvidenceItem.from_operation_result(
            job_id="JOB-001",
            agent_id="agent-abc",
            operation_id="op-001",
            operation_type="system.info",
            data={"hostname": "host1"},
        )
        package = EvidencePackage.build(
            job_id="JOB-001",
            agent_id="agent-abc",
            investigation_id="INV-001",
            started_at="2026-01-01T00:00:00+00:00",
            completed_at="2026-01-01T00:01:00+00:00",
            status="completed",
            operation_results=[],
            evidence_items=[item],
        )
        d = package.to_dict()
        for key in ("schema_version", "job_id", "agent_id", "investigation_id",
                    "started_at", "completed_at", "status", "operations", "evidence", "integrity"):
            assert key in d
        assert d["integrity"]["algorithm"] == "SHA-256"
