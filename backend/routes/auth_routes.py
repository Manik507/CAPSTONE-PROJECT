from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required

from database.db import db
from models.user import User
from models.event import Event
from services.auth_service import authenticate_user, register_user
from services.errors import ApiError
from utils.jwt_handler import create_access_token_for_user, current_user_id


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    user, created = register_user(
        db=db,
        email=data.get("email"),
        username=data.get("username"),
        password=data.get("password"),
        role=data.get("role"),
        full_name=data.get("full_name"),
        phone_number=data.get("phone_number"),
        allow_admin_registration=current_app.config.get("ALLOW_ADMIN_REGISTRATION", False),
    )
    token = create_access_token_for_user(user)
    status = 201 if created else 200
    return jsonify({"user": user.to_dict(), "access_token": token, "created": created}), status


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    portal = data.get("portal")  # Expecting 'PARTICIPANT' or 'INSTITUTE'
    
    user = authenticate_user(db=db, email=data.get("email"), password=data.get("password"))
    
    # Restrict login based on portal
    if portal == "PARTICIPANT":
        if user.role == "VOLUNTEER":
            raise ApiError("Invalid credentials", status_code=401, error="unauthorized")
        if user.role not in ["PARTICIPANT", "ADMIN"]:
            raise ApiError("Invalid credentials", status_code=401, error="unauthorized")
    elif portal == "INSTITUTE":
        if user.role not in ["INSTITUTE", "VOLUNTEER", "ADMIN"]:
            raise ApiError("Invalid credentials", status_code=401, error="unauthorized")
            
    token = create_access_token_for_user(user)
    return jsonify({"user": user.to_dict(), "access_token": token}), 200


@auth_bp.get("/me")
@jwt_required()
def get_me():
    uid = int(current_user_id())
    user = User.query.get(uid)
    if not user:
        raise ApiError("User not found", status_code=404)
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.patch("/update")
@jwt_required()
def update_profile():
    uid = int(current_user_id())
    user = User.query.get(uid)
    if not user:
        raise ApiError("User not found", status_code=404)

    data = request.get_json(silent=True) or {}
    
    # Validation for unique fields if changed
    new_username = data.get("username", "").strip().lower()
    if new_username and new_username != user.username:
        if User.query.filter_by(username=new_username).first():
            raise ApiError("User with this username already exists.", status_code=409)
        user.username = new_username

    new_full_name = data.get("full_name", "").strip()
    if new_full_name:
        user.full_name = new_full_name

    new_phone = data.get("phone_number", "").strip()
    if new_phone:
        if user.role == "PARTICIPANT" and len(new_phone) != 10:
            raise ApiError("A valid 10-digit phone number is required", status_code=400)
        
        # Check uniqueness for phone
        existing_phone = User.query.filter(User.phone_number == new_phone, User.id != uid).first()
        if existing_phone:
            raise ApiError("Phone number already registered", status_code=409)
        user.phone_number = new_phone

    db.session.commit()

    # Share with organizer/volunteer if it's a participant and they have currently active events
    if user.role == "PARTICIPANT" and new_phone:
        from models.participant import Participant
        from models.notification import Notification
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        # Find all active events the user is registered for
        active_participations = Participant.query.join(Participant.event).filter(
            Participant.user_id == uid,
            Participant.event.has(db.and_(Event.date <= now, Event.end_date >= now))
        ).all()

        for p in active_participations:
            # Notify the Institute (Organizer)
            organizer_user_id = p.event.institute.user_id
            notif = Notification(
                user_id=organizer_user_id,
                title="Participant Profile Updated",
                message=f"Participant {user.full_name} (@{user.username}) updated their phone number to {user.phone_number} during the active event '{p.event.title}'.",
                type="PROFILE_UPDATE"
            )
            db.session.add(notif)
            
            # Notify Volunteers
            from models.volunteer import Volunteer
            vols = Volunteer.query.filter_by(event_id=p.event_id).all()
            for v in vols:
                notif_vol = Notification(
                    user_id=v.user_id,
                    title="Participant Profile Updated",
                    message=f"Participant {user.full_name} (@{user.username}) updated their phone number to {user.phone_number} during the active event '{p.event.title}'.",
                    type="PROFILE_UPDATE"
                )
                db.session.add(notif_vol)

    db.session.commit()
    return jsonify({"message": "Profile updated", "user": user.to_dict()}), 200
