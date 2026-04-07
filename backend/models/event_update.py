from datetime import datetime, timezone
from database.db import db

class EventUpdate(db.Model):
    __tablename__ = "event_updates"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    event = db.relationship("Event", backref=db.backref("updates", lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
