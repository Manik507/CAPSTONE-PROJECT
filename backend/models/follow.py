from datetime import datetime, timezone
from database.db import db


class Follow(db.Model):
    __tablename__ = "follows"
    __table_args__ = (
        db.UniqueConstraint("follower_id", "followed_id", name="unique_follow"),
    )

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    followed_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    follower = db.relationship("User", foreign_keys=[follower_id], backref=db.backref("following", lazy="dynamic", cascade="all, delete-orphan"))
    followed = db.relationship("User", foreign_keys=[followed_id], backref=db.backref("followers", lazy="dynamic", cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "follower_id": self.follower_id,
            "followed_id": self.followed_id,
            "followed_name": self.followed.full_name if self.followed else None,
            "followed_username": self.followed.username if self.followed else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
