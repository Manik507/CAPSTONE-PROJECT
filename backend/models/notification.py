import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from database.db import db


class Notification(db.Model):
    __tablename__ = "notifications"

    notification_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=True, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            "notification_id": str(self.notification_id),
            "user_id": str(self.user_id),
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

