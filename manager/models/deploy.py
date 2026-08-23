from . import db
from datetime import datetime
import uuid  # <-- ADD THIS

class Deploy(db.Model):
    __tablename__ = "deploys"

    deploy_id = db.Column(db.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    script_id = db.Column(db.String(64), db.ForeignKey("scripts.script_id"), nullable=False)
    agent_id = db.Column(db.String(64), db.ForeignKey("agents.agent_id"), nullable=False)
    status = db.Column(db.String(16), default="pending")
    deployed_at = db.Column(db.DateTime, default=datetime.utcnow)
    executed_at = db.Column(db.DateTime, nullable=True)
    result_id = db.Column(db.String(64), db.ForeignKey("results.result_id"), nullable=True)

    def to_dict(self):
        return {
            "deploy_id": self.deploy_id,
            "script_id": self.script_id,
            "agent_id": self.agent_id,
            "status": self.status,
            "deployed_at": self.deployed_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "result_id": self.result_id
        }