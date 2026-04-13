from database.db import db
from models.user import User
from app import create_app

app = create_app()
email_to_delete = "v@gmail.com"

with app.app_context():
    user = User.query.filter_by(email=email_to_delete).first()
    if user:
        print(f"Found user: {user.username} ({user.email}). Deleting...")
        db.session.delete(user)
        db.session.commit()
        print("User deleted successfully.")
    else:
        print(f"No user found with email: {email_to_delete}")
