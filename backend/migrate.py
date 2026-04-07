from app import create_app
from database.db import db
from sqlalchemy import text
import random

app = create_app()
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(15) UNIQUE;"))
        db.session.commit()
        print("Column added.")
    except Exception as e:
        db.session.rollback()
        print("Column might exist:", e)

    users = db.session.execute(text("SELECT id FROM users")).fetchall()
    for u in users:
        phone = f"98{str(random.randint(10000000, 99999999))}"
        db.session.execute(text(f"UPDATE users SET phone_number='{phone}' WHERE id={u[0]} AND phone_number IS NULL;"))
    db.session.commit()
    print("Migration complete.")
