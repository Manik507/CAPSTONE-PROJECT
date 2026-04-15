"""
Migration: Add payment_type and transaction_id columns to participants table.
"""
from app import create_app
from database.db import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text(
            "ALTER TABLE participants ADD COLUMN payment_type VARCHAR(20) NOT NULL DEFAULT 'OFFLINE';"
        ))
        db.session.commit()
        print("[OK] Column payment_type added to participants.")
    except Exception as e:
        db.session.rollback()
        print("[SKIP] payment_type:", e)

    try:
        db.session.execute(text(
            "ALTER TABLE participants ADD COLUMN transaction_id VARCHAR(128);"
        ))
        db.session.commit()
        print("[OK] Column transaction_id added to participants.")
    except Exception as e:
        db.session.rollback()
        print("[SKIP] transaction_id:", e)

    print("Payment fields migration complete.")
