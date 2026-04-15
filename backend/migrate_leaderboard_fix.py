"""
Migration: Add missing badge and rank columns to leaderboard table.
"""
from app import create_app
from database.db import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE leaderboard ADD COLUMN badge VARCHAR(20) NOT NULL DEFAULT 'Wood';"))
        db.session.commit()
        print("[OK] Column badge added to leaderboard.")
    except Exception as e:
        db.session.rollback()
        print("[SKIP] badge column might exist:", e)

    try:
        db.session.execute(text("ALTER TABLE leaderboard ADD COLUMN rank INTEGER;"))
        db.session.commit()
        print("[OK] Column rank added to leaderboard.")
    except Exception as e:
        db.session.rollback()
        print("[SKIP] rank column might exist:", e)

    print("Leaderboard migration complete.")
