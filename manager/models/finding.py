from datetime import datetime
import uuid
from models import db


class Finding(db.Model):
    __tablename__ = "findings"

    finding_id = db.Column(db.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    result_id = db.Column(db.String(64), db.ForeignKey("results.result_id"), nullable=False)
    agent_id = db.Column(db.String(64), db.ForeignKey("agents.agent_id"), nullable=False)
    severity = db.Column(db.String(16), nullable=False, default="medium")
    category = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    evidence = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="open")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "finding_id": self.finding_id,
            "result_id": self.result_id,
            "agent_id": self.agent_id,
            "severity": self.severity,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
