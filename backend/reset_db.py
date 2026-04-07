import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database.db import db
import models

app = create_app()

with app.app_context():
    print("Dropping schema public cascade...")
    db.session.execute(db.text("DROP SCHEMA public CASCADE;"))
    db.session.execute(db.text("CREATE SCHEMA public;"))
    db.session.commit()
    print("Schema dropped and recreated. Creating tables...")
    db.create_all()
    print("Tables created!")
