"""
Migration: Create round_locks table and add results_locked column to events.

Run this once to apply the round-locking and results-locking schema changes.
"""
from app import create_app
from database.db import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # 1. Create round_locks table
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS round_locks (
                id SERIAL PRIMARY KEY,
                event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                round_number INTEGER NOT NULL,
                locked_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                locked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                CONSTRAINT unique_event_round_lock UNIQUE (event_id, round_number)
            );
        """))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS ix_round_locks_event_id ON round_locks (event_id);"))
        db.session.commit()
        print("✅ Table round_locks created.")
    except Exception as e:
        db.session.rollback()
        print("⚠️  round_locks table might already exist:", e)

    # 2. Add results_locked column to events
    try:
        db.session.execute(text("ALTER TABLE events ADD COLUMN results_locked BOOLEAN NOT NULL DEFAULT FALSE;"))
        db.session.commit()
        print("✅ Column results_locked added to events.")
    except Exception as e:
        db.session.rollback()
        print("⚠️  results_locked column might already exist:", e)

    print("\n🎉 Migration complete.")
