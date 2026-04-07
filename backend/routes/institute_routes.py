from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from database.db import db
from models.institute import Institute
from models.user import User
from services.errors import ApiError
from utils.decorators import role_required
from utils.jwt_handler import current_user_id


institute_bp = Blueprint("institutes", __name__, url_prefix="/institutes")


@institute_bp.post("/apply")
@jwt_required()
@role_required("INSTITUTE")
def apply_institute():
    uid = int(current_user_id())
    user = User.query.get(uid)
    if not user:
        raise ApiError("User not found", status_code=404)

    existing = Institute.query.filter_by(user_id=uid).first()
    if existing:
        return jsonify({"institute": existing.to_dict(), "message": "Already applied"}), 200

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or user.email).strip()
    details = (data.get("details") or "").strip()

    if not name:
        raise ApiError("Institute name is required", status_code=400)

    institute = Institute(user_id=uid, name=name, email=email, details=details)
    db.session.add(institute)
    db.session.commit()
    return jsonify({"institute": institute.to_dict()}), 201


@institute_bp.get("/status")
@jwt_required()
@role_required("INSTITUTE")
def institute_status():
    uid = int(current_user_id())
    institute = Institute.query.filter_by(user_id=uid).first()
    if not institute:
        return jsonify({"institute": None, "message": "No application found"}), 200
    return jsonify({"institute": institute.to_dict()}), 200


@institute_bp.get("/<int:inst_id>")
@jwt_required()
@role_required("ADMIN")
def get_institute_details(inst_id):
    institute = Institute.query.get(inst_id)
    if not institute:
        raise ApiError("Institute not found", status_code=404)
    return jsonify({"institute": institute.to_dict()}), 200


@institute_bp.patch("/update")
@jwt_required()
@role_required("INSTITUTE")
def update_institute_details():
    uid = int(current_user_id())
    institute = Institute.query.filter_by(user_id=uid).first()
    if not institute:
        raise ApiError("Institute not found", status_code=404)

    data = request.get_json(silent=True) or {}
    new_name = (data.get("name") or "").strip()
    new_email = (data.get("email") or "").strip().lower()
    new_details = (data.get("details") or "").strip()

    if new_name:
        institute.name = new_name
    if new_email:
        institute.email = new_email
    if new_details:
        institute.details = new_details

    db.session.commit()
    return jsonify({"institute": institute.to_dict(), "message": "Institute details updated successfully"}), 200


@institute_bp.post("/events/<int:event_id>/updates")
@jwt_required()
@role_required("INSTITUTE", "ADMIN", "VOLUNTEER")
def post_event_update(event_id):
    from models.event import Event
    from models.event_update import EventUpdate
    from models.participant import Participant
    from models.notification import Notification

    uid = int(current_user_id())
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)

    # Check ownership
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    user = User.query.get(uid)
    
    if user.role == "VOLUNTEER":
        from models.volunteer import Volunteer
        v = Volunteer.query.filter_by(user_id=uid, event_id=event_id).first()
        if not v:
            raise ApiError("Not authorized for this event", status_code=403)
        if event.end_date and event.end_date.replace(tzinfo=timezone.utc) < now:
            raise ApiError("Cannot post updates for a completed event", status_code=403)

    elif user.role == "INSTITUTE":
        institute = Institute.query.filter_by(user_id=uid).first()
        if not institute or event.institute_id != institute.id:
            raise ApiError("Not authorized to post updates for this event", status_code=403)

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        raise ApiError("Message is required", status_code=400)

    # Create event update
    update = EventUpdate(event_id=event_id, message=message)
    db.session.add(update)

    # Also create a notification for all PAID participants of this event
    paid_participants = Participant.query.filter_by(event_id=event_id, payment_status="PAID").all()
    for p in paid_participants:
        notif = Notification(
            user_id=p.user_id,
            title=f"Update for {event.title}",
            message=message,
            type="EVENT_UPDATE"
        )
        db.session.add(notif)

    db.session.commit()
    return jsonify({"message": "Update posted successfully", "update": update.to_dict()}), 201


@institute_bp.post("/events/<int:event_id>/qualify")
@jwt_required()
@role_required("INSTITUTE", "VOLUNTEER")
def qualify_participants(event_id):
    from models.event import Event
    from models.participant import Participant
    from models.notification import Notification

    uid = int(current_user_id())
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)

    # Check ownership
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    user = User.query.get(uid)
    
    if user.role == "VOLUNTEER":
        from models.volunteer import Volunteer
        v = Volunteer.query.filter_by(user_id=uid, event_id=event_id).first()
        if not v:
            raise ApiError("Not authorized for this event", status_code=403)
        if event.end_date and event.end_date.replace(tzinfo=timezone.utc) < now:
            raise ApiError("Cannot qualify participants for a completed event", status_code=403)

    elif user.role == "INSTITUTE":
        institute = Institute.query.filter_by(user_id=uid).first()
        if not institute or event.institute_id != institute.id:
            raise ApiError("Not authorized", status_code=403)

    data = request.get_json(silent=True) or {}
    user_ids = data.get("user_ids", [])
    target_round = data.get("target_round")

    if not user_ids or not target_round:
        raise ApiError("user_ids and target_round are required", status_code=400)

    if target_round > event.num_rounds:
        raise ApiError(f"Event only has {event.num_rounds} rounds", status_code=400)

    # Filter to only PAID participants among the provided IDs
    participants = Participant.query.filter(
        Participant.event_id == event_id,
        Participant.user_id.in_(user_ids)
    ).all()

    qualified_count = 0
    for p in participants:
        if p.payment_status != "PAID":
            continue
        p.qualified_round = target_round
        qualified_count += 1
        
        # Notify the user
        notif = Notification(
            user_id=p.user_id,
            title=f"Round Progression: {event.title}",
            message=f"Congratulations! You have qualified for Round {target_round}.",
            type="ROUND_QUALIFIED"
        )
        db.session.add(notif)


@institute_bp.post("/volunteers/create")
@jwt_required()
@role_required("INSTITUTE")
def create_volunteer():
    from models.volunteer import Volunteer
    from services.auth_service import register_user
    from models.event import Event
    
    uid = int(current_user_id())
    institute = Institute.query.filter_by(user_id=uid).first()
    if not institute:
        raise ApiError("No institute application found", status_code=404)

    data = request.json or {}
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")
    event_id = data.get("event_id")

    if not email or not event_id:
        raise ApiError("Email and Event ID are required", status_code=400)

    event = Event.query.get(event_id)
    if not event or event.institute_id != institute.id:
        raise ApiError("Invalid event ID or unauthorized", status_code=403)

    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        # Register the user as a VOLUNTEER (requires password and name)
        if not password or not full_name:
            raise ApiError("Password and Name are required for NEW volunteers", status_code=400)
        
        username = f"vol_{email.split('@')[0]}"
        try:
            user, _ = register_user(db=db, email=email, username=username, password=password, role="VOLUNTEER", full_name=full_name)
        except ApiError as e:
            raise e
    else:
        # Ensure the user has VOLUNTEER role
        if user.role != "VOLUNTEER":
            raise ApiError("This user exists but is not a volunteer", status_code=400)
    
    # Check if already assigned to this event
    existing_v = Volunteer.query.filter_by(user_id=user.id, event_id=event_id).first()
    if existing_v:
        return jsonify({"message": "Volunteer already assigned to this event", "volunteer": existing_v.to_dict()}), 200

    # Create Volunteer link
    v = Volunteer(user_id=user.id, event_id=event_id, institute_id=institute.id)
    db.session.add(v)
    db.session.commit()

    return jsonify({"message": "Volunteer assigned successfully", "volunteer": v.to_dict()}), 201


@institute_bp.get("/volunteers/all")
@jwt_required()
@role_required("INSTITUTE", "VOLUNTEER")
def get_all_volunteers():
    from models.volunteer import Volunteer
    uid = int(current_user_id())
    from models.user import User
    user = User.query.get(uid)

    if user.role == "VOLUNTEER":
        # Get all events this volunteer is assigned to
        my_assignments = Volunteer.query.filter_by(user_id=uid).all()
        event_ids = [v.event_id for v in my_assignments]
        
        # Find all volunteers assigned to the same events
        vols = Volunteer.query.filter(Volunteer.event_id.in_(event_ids)).all()
        return jsonify({"volunteers": [v.to_dict() for v in vols]}), 200

    institute = Institute.query.filter_by(user_id=uid).first()
    if not institute:
        return jsonify({"volunteers": []}), 200

    vols = Volunteer.query.filter_by(institute_id=institute.id).all()
    if not vols:
        return jsonify({"volunteers": [], "message": "No volunteers available"}), 200
    return jsonify({"volunteers": [v.to_dict() for v in vols]}), 200
