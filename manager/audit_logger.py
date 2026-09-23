"""
Proteus Manager — Structured Audit Logger (Priority 10)

Records security-relevant events for the PROTEUS platform.
Events are structured JSON objects emitted to the Python logging system.

NEVER logs: authentication tokens, passwords, private keys, or credentials.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Optional
from flask import current_app, has_app_context

_audit_logger = logging.getLogger("proteus.audit")


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

    _audit_logger.info(json.dumps(record))
    if has_app_context():
        socketio = current_app.extensions.get("socketio")
        if socketio:
            socketio.emit("audit_event", record)
