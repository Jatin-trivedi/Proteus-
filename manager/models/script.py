from models import db
from datetime import datetime
import uuid

class Script(db.Model):
    __tablename__ = "scripts"

    script_id = db.Column(db.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.Text, nullable=False)
    hash_before = db.Column(db.String(64))
    hash_after = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "script_id": self.script_id,
            "name": self.name,
            "code": self.code,
            "hash_before": self.hash_before,
            "hash_after": self.hash_after,
            "created_at": self.created_at.isoformat()
        }