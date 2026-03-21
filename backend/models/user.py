import uuid
from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID

from database.db import bcrypt, db


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = db.Column(String(255), nullable=False)
    email = db.Column(String(255), nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(String(32), nullable=True, default="ATTENDEE")  # ADMIN|ORGANIZER|ATTENDEE

    created_at = db.Column(db.DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc))

    # Relationships
    events = db.relationship("Event", back_populates="organizer", cascade="all, delete-orphan")
    bookings = db.relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    tickets = db.relationship("Ticket", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, raw_password: str):
        """Hash and store a password."""
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        """Verify a password."""
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def to_public_dict(self):
        """Public-safe representation (never includes password hash)."""
        return {
            "id": str(self.user_id),
            "user_id": str(self.user_id),
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
