from datetime import datetime, timezone
from database.db import db

class Volunteer(db.Model):
    __tablename__ = "volunteers"
    __table_args__ = (
        db.UniqueConstraint("user_id", "event_id", name="unique_volunteer_event"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    institute_id = db.Column(db.Integer, db.ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    task = db.Column(db.String(500), nullable=True) # Role/Task description
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref=db.backref("volunteering", lazy="dynamic", cascade="all, delete-orphan"))
    event = db.relationship("Event", backref=db.backref("volunteers", lazy="dynamic", cascade="all, delete-orphan"))
    institute = db.relationship("Institute", backref=db.backref("volunteers", lazy="dynamic", cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "institute_id": self.institute_id,
            "user_name": self.user.full_name if self.user else None,
            "user_username": self.user.username if self.user else None,
            "user_email": self.user.email if self.user else None,
            "event_title": self.event.title if self.event else None,
            "task": self.task,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
