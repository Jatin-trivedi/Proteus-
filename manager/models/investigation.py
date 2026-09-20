"""
Investigation model — tracks forensic investigations.
"""

from datetime import datetime, timezone
import uuid

try:
    from models import db
except ImportError:
    from manager.models import db


def _utc_now():
    return datetime.now(timezone.utc)


class InvestigationStatus:
    """Enumeration of valid investigation statuses."""
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    ALL = {CREATED, IN_PROGRESS, COMPLETED, FAILED}


class Investigation(db.Model):
    __tablename__ = "investigations"
    __table_args__ = {"extend_existing": True}

    investigation_id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(16), nullable=False, default=InvestigationStatus.CREATED)
    created_at = db.Column(db.DateTime, nullable=False, default=_utc_now)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, name, description=None, investigation_id=None, status=None):
        self.investigation_id = investigation_id or f"INV-{uuid.uuid4().hex[:12]}"
        self.name = name
        self.description = description
        self.status = status or InvestigationStatus.CREATED
        self.created_at = _utc_now()
        self.completed_at = None

    def to_dict(self):
        return {
            "investigation_id": self.investigation_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
