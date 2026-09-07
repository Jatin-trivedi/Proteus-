from datetime import datetime
import uuid
from models import db


class Report(db.Model):
    __tablename__ = "reports"

    report_id = db.Column(db.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    report_type = db.Column(db.String(64), nullable=False, default="full")
    filters = db.Column(db.JSON, nullable=True)
    content = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "report_id": self.report_id,
            "name": self.name,
            "report_type": self.report_type,
            "filters": self.filters,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }
