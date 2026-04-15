"""
RoundLock model — tracks which rounds of an event have been permanently locked.

Once a round is locked, its participant selections are immutable.
Locking is sequential: Round N can only be locked after Round N-1.
First-come-first-lock: whoever (institute or volunteer) submits first
locks the round for everyone.
"""
from datetime import datetime, timezone
from database.db import db


class RoundLock(db.Model):
    __tablename__ = "round_locks"
    __table_args__ = (
        db.UniqueConstraint("event_id", "round_number", name="unique_event_round_lock"),
    )

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    round_number = db.Column(db.Integer, nullable=False)
    locked_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    locked_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    event = db.relationship("Event", backref=db.backref("round_locks", lazy=True, cascade="all, delete-orphan"))
    locker = db.relationship("User", backref=db.backref("round_locks_made", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "round_number": self.round_number,
            "locked_by": self.locked_by,
            "locker_name": self.locker.full_name if self.locker else None,
            "locked_at": self.locked_at.isoformat() if self.locked_at else None,
        }
