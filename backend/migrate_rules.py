from app import create_app
from database.db import db
from sqlalchemy import text

app = create_app()

def run_migration():
    with app.app_context():
        try:
            db.session.execute(text("ALTER TABLE events ADD COLUMN rules TEXT;"))
            db.session.commit()
            print("Successfully added rules column.")
        except Exception as e:
            db.session.rollback()
            print("Migration failed:", e)

if __name__ == '__main__':
    run_migration()
