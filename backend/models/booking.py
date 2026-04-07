import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID
from database.db import db


class Booking(db.Model):
    __tablename__ = "bookings"

    __table_args__ = (
        db.UniqueConstraint('user_id', 'event_id', name='unique_user_event_booking'),
    )

    # ✅ PRIMARY KEY (FIXED)
    booking_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # ✅ FOREIGN KEYS
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ✅ OTHER FIELDS
    booking_date = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="ACTIVE"   # ACTIVE | CANCELLED
    )

    # ✅ RELATIONSHIPS
    user = db.relationship("User", backref="bookings")
    event = db.relationship("Event", backref="bookings")
    ticket = db.relationship(
        "Ticket",
        back_populates="booking",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # ✅ SERIALIZER
    def to_dict(self, include_event=False):
        payload = {
            "booking_id": str(self.booking_id),
            "user_id": str(self.user_id),
            "event_id": str(self.event_id),
            "booking_time": self.booking_date.isoformat() if self.booking_date else None,
            "status": self.status,
            "ticket_id": str(self.ticket.ticket_id) if self.ticket else None,
        }

        if include_event and self.event:
            payload["event"] = self.event.to_dict(include_organizer=False)

        return payload


class Ticket(db.Model):
    __tablename__ = "tickets"

    # ✅ PRIMARY KEY
    ticket_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    ticket_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    # ✅ FOREIGN KEYS
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    booking_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("bookings.booking_id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
        index=True
    )

    # ✅ OTHER FIELDS
    booking_time = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    check_in_status = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    # ✅ RELATIONSHIPS
    booking = db.relationship("Booking", back_populates="ticket")
    user = db.relationship("User", backref="tickets")
    event = db.relationship("Event", backref="tickets")

    # ✅ SERIALIZER
    def to_dict(self):
        return {
            "ticket_id": str(self.ticket_id),
            "user_id": str(self.user_id),
            "event_id": str(self.event_id),
            "booking_id": str(self.booking_id) if self.booking_id else None,
            "booking_time": self.booking_time.isoformat() if self.booking_time else None,
            "check_in_status": self.check_in_status,
        }