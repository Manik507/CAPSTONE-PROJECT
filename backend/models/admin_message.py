from datetime import datetime, timezone
from database.db import db

class AdminMessage(db.Model):
    __tablename__ = "admin_messages"

    id = db.Column(db.Integer, primary_key=True)
    institute_id = db.Column(db.Integer, db.ForeignKey("institutes.id", ondelete="CASCADE"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    reply = db.Column(db.Text, nullable=True)
    replied_by_admin_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    replied_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Relationships
    institute = db.relationship("Institute", backref=db.backref("admin_messages", lazy=True, cascade="all, delete-orphan"))
    admin = db.relationship("User", backref=db.backref("admin_replies", lazy=True))

    def to_dict(self, include_admin_details=False):
        data = {
            "id": self.id,
            "institute_id": self.institute_id,
            "institute_name": self.institute.name if self.institute else None,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reply": self.reply,
            "replied_at": self.replied_at.isoformat() if self.replied_at else None,
        }
        if include_admin_details and self.replied_by_admin_id:
            data["replied_by_admin_name"] = self.admin.full_name if self.admin else "Unknown Admin"
            data["replied_by_admin_email"] = self.admin.email if self.admin else None
        elif self.replied_by_admin_id:
            data["replied_by_admin_name"] = "Admin"
        else:
            data["replied_by_admin_name"] = None
        return data
