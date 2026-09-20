"""
Job model — tracks forensic investigation jobs assigned to agents.

Implements a strict state machine for job lifecycle:
  QUEUED → ASSIGNED → RUNNING → COMPLETED
                               → FAILED
  QUEUED → CANCELLED
  ASSIGNED → CANCELLED
"""

from datetime import datetime, timezone
import json
import uuid

try:
    from models import db
except ImportError:
    from manager.models import db


def _utc_now():
    return datetime.now(timezone.utc)


class JobStatus:
    """Enumeration of valid job statuses."""
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    ALL = {QUEUED, ASSIGNED, RUNNING, COMPLETED, FAILED, CANCELLED}
    TERMINAL = {COMPLETED, FAILED, CANCELLED}

    # Valid state transitions: source → {allowed targets}
    TRANSITIONS = {
        QUEUED: {ASSIGNED, CANCELLED},
        ASSIGNED: {RUNNING, CANCELLED},
        RUNNING: {COMPLETED, FAILED},
        COMPLETED: set(),
        FAILED: set(),
        CANCELLED: set(),
    }

    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """Returns True if the transition from from_status to to_status is valid."""
        allowed = cls.TRANSITIONS.get(from_status, set())
        return to_status in allowed


class JobTransitionError(ValueError):
    """Raised when an invalid job state transition is attempted."""
    pass


class Job(db.Model):
    __tablename__ = "jobs"
    __table_args__ = {"extend_existing": True}

    job_id = db.Column(db.String(64), primary_key=True)
    agent_id = db.Column(db.String(64), db.ForeignKey("agents.agent_id"), nullable=False)
    investigation_id = db.Column(db.String(64), nullable=False)
    ir = db.Column(db.Text, nullable=False)  # JSON-serialized IR document
    status = db.Column(db.String(16), nullable=False, default=JobStatus.QUEUED)
    created_at = db.Column(db.DateTime, nullable=False, default=_utc_now)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    error = db.Column(db.Text, nullable=True)

    # Relationship
    agent = db.relationship("Agent", backref="jobs")

    def __init__(
        self,
        agent_id,
        investigation_id,
        ir,
        job_id=None,
        status=None,
    ):
        self.job_id = job_id or f"JOB-{uuid.uuid4().hex[:12]}"
        self.agent_id = agent_id
        self.investigation_id = investigation_id

        if isinstance(ir, dict):
            self.ir = json.dumps(ir, sort_keys=True)
        elif isinstance(ir, str):
            # Validate it's parseable JSON
            json.loads(ir)
            self.ir = ir
        else:
            raise ValueError(f"IR must be a dict or JSON string, got {type(ir).__name__}")

        self.status = status or JobStatus.QUEUED
        self.created_at = _utc_now()
        self.started_at = None
        self.completed_at = None
        self.error = None

    def transition_to(self, new_status: str, error: str = None):
        """
        Attempt a state transition. Raises JobTransitionError if invalid.
        Automatically sets started_at/completed_at timestamps.
        """
        if not JobStatus.can_transition(self.status, new_status):
            raise JobTransitionError(
                f"Invalid job transition: {self.status} → {new_status}. "
                f"Allowed: {sorted(JobStatus.TRANSITIONS.get(self.status, set()))}"
            )

        self.status = new_status

        if new_status == JobStatus.RUNNING:
            self.started_at = _utc_now()
        elif new_status in JobStatus.TERMINAL:
            self.completed_at = _utc_now()
            if error:
                self.error = str(error)

    def get_ir_dict(self) -> dict:
        """Deserialize and return the IR as a dictionary."""
        try:
            return json.loads(self.ir)
        except (json.JSONDecodeError, TypeError):
            return {}

    def to_dict(self):
        return {
            "job_id": self.job_id,
            "agent_id": self.agent_id,
            "investigation_id": self.investigation_id,
            "ir": self.get_ir_dict(),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }
