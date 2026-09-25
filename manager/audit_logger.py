"""
Proteus Manager — Structured Audit Logger (Priority 10)

Records security-relevant events for the PROTEUS platform.
Events are structured JSON objects emitted to the Python logging system.

NEVER logs: authentication tokens, passwords, private keys, or credentials.
"""

from datetime import datetime, timezone
import copy
import fcntl
import hashlib
import json
import logging
import os
from pathlib import Path
import threading
from typing import Any, Optional
from flask import current_app, has_app_context

_audit_logger = logging.getLogger("proteus.audit")
_audit_write_lock = threading.Lock()
_GENESIS_HASH = "0" * 64


class AuditLogIntegrityError(RuntimeError):
    """Raised when the persisted audit chain is malformed or tampered with."""


class AuditEvent:
    """Known audit event types."""
    AGENT_REGISTERED = "AGENT_REGISTERED"
    AGENT_HEARTBEAT = "AGENT_HEARTBEAT"
    AGENT_OFFLINE = "AGENT_OFFLINE"
    JOB_CREATED = "JOB_CREATED"
    JOB_ASSIGNED = "JOB_ASSIGNED"
    JOB_STARTED = "JOB_STARTED"
    JOB_COMPLETED = "JOB_COMPLETED"
    JOB_FAILED = "JOB_FAILED"
    JOB_CANCELLED = "JOB_CANCELLED"
    RESULT_UPLOADED = "RESULT_UPLOADED"
    INVALID_IR_REJECTED = "INVALID_IR_REJECTED"
    UNAUTHORIZED_REQUEST = "UNAUTHORIZED_REQUEST"
    INVESTIGATION_CREATED = "INVESTIGATION_CREATED"
    EVIDENCE_STORED = "EVIDENCE_STORED"


def _sanitize(value: Any) -> Any:
    """
    Ensures no sensitive values are logged.
    Redacts fields commonly used for credentials.
    """
    if isinstance(value, dict):
        redacted = {}
        for k, v in value.items():
            key_lower = k.lower()
            if any(s in key_lower for s in ("token", "password", "secret", "key", "credential", "auth")):
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = _sanitize(v)
        return redacted
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    return value


def _canonical_json(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _audit_log_path() -> Path:
    if has_app_context():
        configured_path = current_app.config.get("AUDIT_LOG_PATH")
    else:
        configured_path = os.getenv("AUDIT_LOG_PATH")
    return Path(configured_path or Path(__file__).with_name("audit.log"))


def _read_chain(path: Path) -> list[dict]:
    if not path.exists():
        return []

    records = []
    previous_hash = _GENESIS_HASH
    for expected_sequence, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise AuditLogIntegrityError(f"Invalid JSON at audit sequence {expected_sequence}") from error
        if not isinstance(record, dict):
            raise AuditLogIntegrityError(f"Invalid audit record at sequence {expected_sequence}")

        entry_hash = record.pop("entry_hash", None)
        if not isinstance(entry_hash, str):
            raise AuditLogIntegrityError(f"Missing entry hash at audit sequence {expected_sequence}")
        if record.get("sequence") != expected_sequence:
            raise AuditLogIntegrityError(f"Invalid sequence at audit entry {expected_sequence}")
        if record.get("previous_hash") != previous_hash:
            raise AuditLogIntegrityError(f"Broken audit hash link at sequence {expected_sequence}")
        computed_hash = hashlib.sha256(_canonical_json(record).encode("utf-8")).hexdigest()
        if computed_hash != entry_hash:
            raise AuditLogIntegrityError(f"Audit hash mismatch at sequence {expected_sequence}")

        record["entry_hash"] = entry_hash
        records.append(record)
        previous_hash = entry_hash
    return records


def verify_audit_log(path: Optional[str] = None) -> dict:
    """Validate the complete audit chain and return its current sequence state."""
    records = _read_chain(Path(path) if path else _audit_log_path())
    return {
        "valid": True,
        "entries": len(records),
        "last_sequence": records[-1]["sequence"] if records else 0,
        "last_hash": records[-1]["entry_hash"] if records else _GENESIS_HASH,
    }


def _append_record(record: dict) -> dict:
    path = _audit_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(f".{path.name}.lock")

    with _audit_write_lock, lock_path.open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            records = _read_chain(path)
            sealed = {
                **record,
                "sequence": len(records) + 1,
                "previous_hash": records[-1]["entry_hash"] if records else _GENESIS_HASH,
            }
            sealed["entry_hash"] = hashlib.sha256(_canonical_json(sealed).encode("utf-8")).hexdigest()
            encoded = (json.dumps(sealed, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
            descriptor = os.open(path, flags, 0o600)
            try:
                os.write(descriptor, encoded)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            return sealed
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def log_event(
    event_type: str,
    agent_id: Optional[str] = None,
    job_id: Optional[str] = None,
    investigation_id: Optional[str] = None,
    detail: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    """
    Emits a structured audit log event.

    Args:
        event_type:       One of AuditEvent.* constants
        agent_id:         Agent involved (if applicable)
        job_id:           Job involved (if applicable)
        investigation_id: Investigation involved (if applicable)
        detail:           Human-readable description
        extra:            Additional context dict (sanitized before logging)
    """
    record: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
    }
    if agent_id:
        record["agent_id"] = agent_id
    if job_id:
        record["job_id"] = job_id
    if investigation_id:
        record["investigation_id"] = investigation_id
    if detail:
        record["detail"] = detail
    if extra:
        record["extra"] = _sanitize(extra)

    sealed_record = _append_record(record)
    _audit_logger.info(json.dumps(sealed_record))
    if has_app_context():
        socketio = current_app.extensions.get("socketio")
        if socketio:
            socketio.emit("audit_event", sealed_record)


def get_audit_events(
    agent_id: Optional[str] = None,
    event_type: Optional[str] = None,
) -> list[dict]:
    """Return persisted structured audit events matching the supplied filters."""
    events = _read_chain(_audit_log_path())
    if agent_id:
        events = [event for event in events if event.get("agent_id") == agent_id]
    if event_type:
        events = [event for event in events if event.get("event_type") == event_type]
    return [copy.deepcopy(event) for event in reversed(events)]
