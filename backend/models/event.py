from datetime import datetime, timezone

from database.db import db


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    rules = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=100)
    image_url = db.Column(db.Text, nullable=True)
    qr_code_url = db.Column(db.Text, nullable=True)
    approval_status = db.Column(db.String(20), nullable=False, default="PENDING")  # PENDING | APPROVED | REJECTED
    
    # Advanced Event Management
    end_date = db.Column(db.DateTime(timezone=True), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    extra_locations = db.Column(db.Text, nullable=True)
    num_rounds = db.Column(db.Integer, nullable=False, default=1)
    fees = db.Column(db.Integer, nullable=False, default=0)
    results_locked = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    institute = db.relationship("Institute", back_populates="events")
    participants = db.relationship("Participant", back_populates="event", cascade="all, delete-orphan")


    def to_dict(self):
        return {
            "id": self.id,
            "institute_id": self.institute_id,
            "title": self.title,
            "description": self.description,
            "rules": self.rules,
            "date": self.date.isoformat() if self.date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "extra_locations": self.extra_locations,
            "num_rounds": self.num_rounds,
            "fees": self.fees,
            "image_url": self.image_url,
            "qr_code_url": self.qr_code_url,
            "approval_status": self.approval_status,
            "results_locked": self.results_locked,
            "is_completed": self._is_completed(),
            "institute_name": self.institute.name if self.institute else None,
            "registered_count": len(self.participants) if self.participants else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def _is_completed(self):
        """Return True if the event's end_date has passed."""
        if not self.end_date:
            return False
        now = datetime.now(timezone.utc)
        end = self.end_date
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return end < now
