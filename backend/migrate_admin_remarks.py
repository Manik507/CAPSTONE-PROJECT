from app import create_app
from database.db import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE institutes ADD COLUMN admin_remarks TEXT'))
        db.session.execute(text('ALTER TABLE events ADD COLUMN admin_remarks TEXT'))
        db.session.commit()
        print("Successfully added admin_remarks to institutes and events tables.")
    except Exception as e:
        print(f"Error (column might already exist?): {e}")
