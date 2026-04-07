from datetime import datetime, timezone

from database.db import db


class Participant(db.Model):
    __tablename__ = "participants"
    __table_args__ = (
        db.UniqueConstraint("user_id", "event_id", name="unique_user_event"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_status = db.Column(db.String(20), nullable=False, default="UNPAID")  # PAID | UNPAID
    qualified_round = db.Column(db.Integer, nullable=False, default=1)
    registration_id = db.Column(db.String(64), nullable=True, unique=True)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="participations")
    event = db.relationship("Event", back_populates="participants")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "payment_status": self.payment_status,
            "qualified_round": self.qualified_round,
            "registration_id": self.registration_id,
            "user_name": self.user.full_name if self.user else None,
            "user_username": self.user.username if self.user else None,
            "user_email": self.user.email if self.user else None,
            "user_phone": self.user.phone_number if self.user else None,
            "event_title": self.event.title if self.event else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
