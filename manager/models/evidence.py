"""
Evidence model — tracks forensic evidence items collected during job execution.
Each evidence item is tied to a specific job, agent, and operation, with SHA-256 integrity.
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


class Evidence(db.Model):
    __tablename__ = "evidence"
    __table_args__ = {"extend_existing": True}

    evidence_id = db.Column(db.String(64), primary_key=True)
    job_id = db.Column(db.String(64), db.ForeignKey("jobs.job_id"), nullable=False)
    agent_id = db.Column(db.String(64), db.ForeignKey("agents.agent_id"), nullable=False)
    operation_id = db.Column(db.String(64), nullable=False)
    operation_type = db.Column(db.String(64), nullable=False)
    collected_at = db.Column(db.DateTime, nullable=False, default=_utc_now)
    data = db.Column(db.Text, nullable=False)  # JSON-serialized evidence data
    sha256 = db.Column(db.String(64), nullable=False)
    schema_version = db.Column(db.String(16), nullable=False, default="1.0")

    # Relationships
    job = db.relationship("Job", backref="evidence_items")
    agent = db.relationship("Agent", backref="evidence_items")

    def __init__(
        self,
        job_id,
        agent_id,
        operation_id,
        operation_type,
        data,
        sha256,
        evidence_id=None,
        collected_at=None,
        schema_version="1.0",
    ):
        self.evidence_id = evidence_id or f"EVD-{uuid.uuid4().hex[:12]}"
        self.job_id = job_id
        self.agent_id = agent_id
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.collected_at = collected_at or _utc_now()
        self.schema_version = schema_version

        if isinstance(data, dict):
            self.data = json.dumps(data, sort_keys=True)
        elif isinstance(data, str):
            self.data = data
        else:
            self.data = json.dumps(str(data))

        self.sha256 = sha256

    def get_data_dict(self) -> dict:
        """Deserialize and return the evidence data as a dictionary."""
        try:
            return json.loads(self.data)
        except (json.JSONDecodeError, TypeError):
            return {}

    def to_dict(self):
        return {
            "evidence_id": self.evidence_id,
            "job_id": self.job_id,
            "agent_id": self.agent_id,
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "data": self.get_data_dict(),
            "sha256": self.sha256,
            "schema_version": self.schema_version,
        }
