from database.db import db


class Leaderboard(db.Model):
    __tablename__ = "leaderboard"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    xp = db.Column(db.Integer, nullable=False, default=0)
    trophies = db.Column(db.Integer, nullable=False, default=0)

    rank = db.Column(db.Integer, nullable=True)

    user = db.relationship("User", back_populates="leaderboard_entry")



    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else None,
            "xp": self.xp,
            "trophies": self.trophies,
            "rank": self.rank,
        }
