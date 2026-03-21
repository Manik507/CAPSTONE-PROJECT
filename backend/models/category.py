from database.db import db


class Category(db.Model):
    __tablename__ = "categories"

    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)

    events = db.relationship("Event", back_populates="category")

    def to_dict(self):
        return {"category_id": self.category_id, "name": self.name}

