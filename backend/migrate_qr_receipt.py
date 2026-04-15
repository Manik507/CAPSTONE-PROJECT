from app import create_app
from database.db import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE events ADD COLUMN qr_code_url TEXT;"))
        db.session.commit()
        print("Column qr_code_url added to events.")
    except Exception as e:
        db.session.rollback()
        print("Column qr_code_url might exist:", e)

    try:
        db.session.execute(text("ALTER TABLE participants ADD COLUMN receipt_url TEXT;"))
        db.session.commit()
        print("Column receipt_url added to participants.")
    except Exception as e:
        db.session.rollback()
        print("Column receipt_url might exist:", e)

    print("Migration complete.")
