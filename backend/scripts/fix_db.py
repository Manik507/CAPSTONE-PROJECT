import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database.db import db
from sqlalchemy import text

def fix_database():
    app = create_app()
    with app.app_context():
        # Ensure all tables are created (including the new activity_logs)
        db.create_all()
        print("Ensured all tables are created.")
        
        print("Checking for missing columns in 'participants' table...")
        try:
            # Check if column exists
            query = text("SELECT column_name FROM information_schema.columns WHERE table_name='participants' AND column_name='qualified_round'")
            result = db.session.execute(query).fetchone()
            
            if not result:
                print("Adding 'qualified_round' column to 'participants' table...")
                db.session.execute(text("ALTER TABLE participants ADD COLUMN qualified_round INTEGER NOT NULL DEFAULT 1"))
                db.session.commit()
                print("Successfully added 'qualified_round' column.")
            else:
                print("'qualified_round' column already exists.")
                
            # Check for registration_id as well (just in case)
            query = text("SELECT column_name FROM information_schema.columns WHERE table_name='participants' AND column_name='registration_id'")
            result = db.session.execute(query).fetchone()
            if not result:
                print("Adding 'registration_id' column to 'participants' table...")
                db.session.execute(text("ALTER TABLE participants ADD COLUMN registration_id VARCHAR(64) UNIQUE"))
                db.session.commit()
                print("Successfully added 'registration_id' column.")
            else:
                print("'registration_id' column already exists.")

        except Exception as e:
            print(f"Error fixing database: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    fix_database()
