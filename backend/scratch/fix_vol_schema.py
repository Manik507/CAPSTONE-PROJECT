from app import create_app
from database.db import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE volunteers ADD COLUMN task VARCHAR(500);"))
        db.session.commit()
        print("Column 'task' added to 'volunteers' table.")
    except Exception as e:
        db.session.rollback()
        print("Column might exist or error:", e)
