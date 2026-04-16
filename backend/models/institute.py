from datetime import datetime, timezone

from database.db import db


class Institute(db.Model):
    __tablename__ = "institutes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    approval_status = db.Column(db.String(20), nullable=False, default="PENDING")  # PENDING | APPROVED | REJECTED
    admin_remarks = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="institute")
    events = db.relationship("Event", back_populates="institute", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "name": self.name,
            "email": self.email,
            "details": self.details,
            "approval_status": self.approval_status,
            "admin_remarks": self.admin_remarks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
