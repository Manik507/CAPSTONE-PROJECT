from app import create_app
from database.db import db
from models.user import User

def create_or_update_admin():
    app = create_app()
    with app.app_context():
        email = "admin@gmail.com"
        password = "admin#1234"
        
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                full_name="System Admin",
                username="admin_user_2",
                email=email,
                role="ADMIN"
            )
            user.set_password(password)
            db.session.add(user)
            print("Admin user created successfully.")
        else:
            user.role = "ADMIN"
            user.set_password(password)
            print("Admin user updated successfully.")
            
        db.session.commit()

if __name__ == "__main__":
    create_or_update_admin()
