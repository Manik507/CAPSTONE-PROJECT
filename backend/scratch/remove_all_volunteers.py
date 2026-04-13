from database.db import db
from models.user import User
from models.volunteer import Volunteer
from app import create_app

app = create_app()

with app.app_context():
    # 1. Delete from volunteers table (assignment table)
    deleted_assignments = Volunteer.query.delete()
    
    # 2. Delete from users table where role is VOLUNTEER
    vols = User.query.filter_by(role="VOLUNTEER").all()
    v_count = len(vols)
    for v in vols:
        db.session.delete(v)
    
    db.session.commit()
    print(f"Deleted {v_count} volunteer accounts.")
    print(f"Removed {deleted_assignments} volunteer assignments.")
