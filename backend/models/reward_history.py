from datetime import datetime, timezone
from database.db import db


class RewardHistory(db.Model):
    __tablename__ = "reward_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    reward_type = db.Column(db.String(32), nullable=False)  # PARTICIPATION | WINNING
    xp_awarded = db.Column(db.Integer, nullable=False, default=0)
    trophies_awarded = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref=db.backref("reward_history", lazy=True, cascade="all, delete-orphan"))
    event = db.relationship("Event", backref=db.backref("reward_history", lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "event_title": self.event.title if self.event else None,
            "reward_type": self.reward_type,
            "xp_awarded": self.xp_awarded,
            "trophies_awarded": self.trophies_awarded,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
