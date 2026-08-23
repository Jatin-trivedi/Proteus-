from . import db
from datetime import datetime
import uuid  # <-- ADD THIS LINE

class Script(db.Model):
    __tablename__ = "scripts"

    script_id = db.Column(db.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(128), nullable=False)
    code = db.Column(db.Text, nullable=False)
    hash = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(64), nullable=True)

    def to_dict(self):
        return {
            "script_id": self.script_id,
            "name": self.name,
            "hash": self.hash,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by
        }