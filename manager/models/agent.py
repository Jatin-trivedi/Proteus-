from models import db
from datetime import datetime
import uuid

class Agent(db.Model):
    __tablename__ = "agents"

    agent_id = db.Column(db.String(64), primary_key=True)
    os = db.Column(db.String(32), nullable=False)
    ip = db.Column(db.String(45), nullable=False)
    arch = db.Column(db.String(16), nullable=False)
    status = db.Column(db.String(16), default="offline")
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.String(256), unique=True)

    def __init__(self, agent_id, os, ip, arch):
        self.agent_id = agent_id
        self.os = os
        self.ip = ip
        self.arch = arch
        self.token = self._generate_token()

    @staticmethod
    def _generate_token():
        return uuid.uuid4().hex + uuid.uuid4().hex[:16]

    def update_heartbeat(self):
        self.last_seen = datetime.utcnow()
        self.status = "online"