from datetime import datetime, timezone
from database.db import db


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = db.Column(db.String(64), nullable=False)  # e.g. "EVENT_APPROVED", "EVENT_REJECTED", "INSTITUTE_APPROVED"
    target_id = db.Column(db.Integer, nullable=True)
    target_name = db.Column(db.String(255), nullable=True)
    details = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship
    admin = db.relationship("User", backref=db.backref("activity_logs", lazy="dynamic", cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "action_type": self.action_type,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
