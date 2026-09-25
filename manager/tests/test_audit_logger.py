import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from audit_logger import (
    AuditLogIntegrityError,
    _GENESIS_HASH,
    get_audit_events,
    log_event,
    verify_audit_log,
)


def test_audit_log_is_persistent_hash_chained_and_redacted(tmp_path, monkeypatch):
    log_path = tmp_path / "audit.log"
    monkeypatch.setenv("AUDIT_LOG_PATH", str(log_path))

    log_event(
        "EVIDENCE_STORED",
        agent_id="agent-chain-001",
        extra={"token": "never-persist", "artifact_count": 2},
    )
    log_event("JOB_COMPLETED", agent_id="agent-chain-001")

    state = verify_audit_log()
    assert state["valid"] is True
    assert state["entries"] == 2
    assert state["last_sequence"] == 2

    records = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert records[0]["sequence"] == 1
    assert records[0]["previous_hash"] == _GENESIS_HASH
    assert records[1]["sequence"] == 2
    assert records[1]["previous_hash"] == records[0]["entry_hash"]
    assert records[0]["extra"]["token"] == "[REDACTED]"
    assert "never-persist" not in log_path.read_text()

    events = get_audit_events(agent_id="agent-chain-001")
    assert [event["event_type"] for event in events] == ["JOB_COMPLETED", "EVIDENCE_STORED"]


def test_audit_log_detects_tampering(tmp_path, monkeypatch):
    log_path = tmp_path / "audit.log"
    monkeypatch.setenv("AUDIT_LOG_PATH", str(log_path))
    log_event("JOB_STARTED", job_id="JOB-chain-001")

    record = json.loads(log_path.read_text())
    record["event_type"] = "JOB_CANCELLED"
    log_path.write_text(json.dumps(record) + "\n")

    with pytest.raises(AuditLogIntegrityError, match="hash mismatch"):
        verify_audit_log()
