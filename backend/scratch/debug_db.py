"""Debug: show actual leaderboard columns in the database."""
from app import create_app
from database.db import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    result = db.session.execute(text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = 'leaderboard' ORDER BY ordinal_position;"
    ))
    print("Columns in leaderboard table:")
    for row in result:
        print(f"  {row[0]:20s} {row[1]}")
