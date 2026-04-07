from datetime import datetime, timezone
from database.db import db

class EventResult(db.Model):
    __tablename__ = "event_results"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rank = db.Column(db.Integer, nullable=False, default=1)
    prize_name = db.Column(db.String(255), nullable=False) # e.g. "Winner", "1st Runner Up"
    prize_description = db.Column(db.Text, nullable=True) # e.g. "$500 Cash prize"

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    event = db.relationship("Event", backref=db.backref("event_results", lazy=True, cascade="all, delete-orphan"))
    user = db.relationship("User", backref=db.backref("event_achievements", lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "rank": self.rank,
            "prize_name": self.prize_name,
            "prize_description": self.prize_description,
            "user_name": self.user.full_name if self.user else None,
            "user_email": self.user.email if self.user else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
