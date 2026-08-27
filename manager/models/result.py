from models import db
from datetime import datetime
import uuid  # <-- ADD THIS

class Result(db.Model):
    __tablename__ = "results"

    result_id = db.Column(db.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = db.Column(db.String(64), db.ForeignKey("agents.agent_id"), nullable=False)
    script_id = db.Column(db.String(64), db.ForeignKey("scripts.script_id"), nullable=False)
    data_encrypted = db.Column(db.Text, nullable=False)
    data_decrypted = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "result_id": self.result_id,
            "agent_id": self.agent_id,
            "script_id": self.script_id,
            "submitted_at": self.submitted_at.isoformat(),
            "data_encrypted": self.data_encrypted,
            "data_decrypted": self.data_decrypted
        }