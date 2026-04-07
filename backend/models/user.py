from datetime import datetime, timezone

from database.db import bcrypt, db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(64), nullable=False, unique=True, index=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    phone_number = db.Column(db.String(15), nullable=True, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(32), nullable=False, default="PARTICIPANT")  # ADMIN | INSTITUTE | PARTICIPANT

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    institute = db.relationship("Institute", back_populates="user", uselist=False, cascade="all, delete-orphan")
    participations = db.relationship("Participant", back_populates="user", cascade="all, delete-orphan")
    leaderboard_entry = db.relationship("Leaderboard", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, raw_password: str):
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        # Default to user's full name
        display_name = self.full_name
        # If institute, use official institute name
        if self.role == "INSTITUTE" and self.institute:
            display_name = self.institute.name
            
        return {
            "id": self.id,
            "full_name": display_name,
            "username": self.username,
            "email": self.email,
            "phone_number": self.phone_number,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
