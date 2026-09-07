from datetime import datetime
import uuid
from werkzeug.security import check_password_hash, generate_password_hash
from models import db


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="analyst")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
        }
