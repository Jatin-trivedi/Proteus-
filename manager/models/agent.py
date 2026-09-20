"""
Agent model – tracks registered forensic agents and their status.
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


class Agent(db.Model):
    __tablename__ = "agents"
    __table_args__ = {"extend_existing": True}

    agent_id = db.Column(db.String(64), primary_key=True)
    hostname = db.Column(db.String(100), nullable=False)
    os = db.Column(db.String(32), nullable=False)
    arch = db.Column(db.String(32), nullable=False, default="x86_64")
    version = db.Column(db.String(32), nullable=True, default="1.0.0")
    capabilities = db.Column(db.Text, nullable=True, default="[]")
    status = db.Column(db.String(16), nullable=False, default="ONLINE")
    registered_at = db.Column(db.DateTime, nullable=True, default=_utc_now)
    last_seen = db.Column(db.DateTime, nullable=True, default=_utc_now)
    current_job = db.Column(db.String(64), nullable=True)
    ip = db.Column(db.String(45), nullable=True, default="0.0.0.0")
    token = db.Column(db.String(256), unique=True, nullable=True)

    # Property aliases for full contract compatibility
    @property
    def architecture(self):
        return self.arch

    @architecture.setter
    def architecture(self, value):
        self.arch = value

    @property
    def last_heartbeat(self):
        return self.last_seen

    @last_heartbeat.setter
    def last_heartbeat(self, value):
        self.last_seen = value

    def __init__(
        self,
        agent_id,
        hostname,
        os,
        architecture="x86_64",
        version="1.0.0",
        capabilities=None,
        status="ONLINE",
        ip="0.0.0.0",
        current_job=None,
        arch=None,
    ):
        self.agent_id = agent_id
        self.hostname = hostname
        self.os = os
        self.arch = architecture or arch or "x86_64"
        self.version = version or "1.0.0"

        if capabilities is None:
            self.capabilities = "[]"
        elif isinstance(capabilities, (list, dict)):
            self.capabilities = json.dumps(capabilities)
        else:
            self.capabilities = str(capabilities)

        self.status = status or "ONLINE"
        self.registered_at = _utc_now()
        self.last_seen = _utc_now()
        self.current_job = current_job
        self.ip = ip or "0.0.0.0"
        self.token = self._generate_token()

    @staticmethod
    def _generate_token():
        return uuid.uuid4().hex + uuid.uuid4().hex[:16]

    def update_heartbeat(self, status="ONLINE", current_job=None):
        self.last_seen = _utc_now()
        self.status = status or "ONLINE"
        if current_job is not None:
            self.current_job = current_job

    def get_capabilities_list(self):
        try:
            return json.loads(self.capabilities) if self.capabilities else []
        except Exception:
            return []

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "hostname": self.hostname,
            "os": self.os,
            "architecture": self.arch,
            "arch": self.arch,
            "version": self.version or "1.0.0",
            "capabilities": self.get_capabilities_list(),
            "status": self.status or "ONLINE",
            "registered_at": self.registered_at.isoformat() if self.registered_at else (
                self.last_seen.isoformat() if self.last_seen else None
            ),
            "last_heartbeat": self.last_seen.isoformat() if self.last_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "current_job": self.current_job,
            "ip": self.ip,
        }