import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID

from database.db import db


class Event(db.Model):
    __tablename__ = "events"

    event_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(String(200), nullable=False, index=True)
    description = db.Column(Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.category_id"), nullable=True, index=True)
    event_date = db.Column(db.DateTime(timezone=True), nullable=False)
    location = db.Column(String(255), nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    image_url = db.Column(Text, nullable=True)

    organizer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=True, index=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc))

    organizer = db.relationship("User", back_populates="events")
    category = db.relationship("Category", back_populates="events")
    bookings = db.relationship("Booking", back_populates="event", cascade="all, delete-orphan")
    tickets = db.relationship("Ticket", back_populates="event", cascade="all, delete-orphan")

    def to_dict(self, include_organizer=False, include_capacity=False):
        payload = {
            "id": str(self.event_id),
            "event_id": str(self.event_id),
            "title": self.title,
            "description": self.description,
            "category": self.category.name if self.category else None,
            "category_id": self.category_id,
            "date": self.event_date.isoformat() if self.event_date else None,
            "venue": self.location,
            "max_capacity": self.max_capacity,
            "organizer_id": str(self.organizer_id),
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_organizer and self.organizer:
            payload["organizer"] = self.organizer.to_public_dict()
        if include_capacity:
            # Computed in service; placeholder for API compatibility.
            payload["remaining_capacity"] = None
        return payload
