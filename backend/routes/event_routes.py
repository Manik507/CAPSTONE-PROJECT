from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from database.db import db
from models.event import Event
from models.institute import Institute
from services.errors import ApiError
from utils.decorators import role_required
from utils.jwt_handler import current_user_id


events_bp = Blueprint("events", __name__, url_prefix="/events")


def _parse_iso_datetime(value):
    try:
        if isinstance(value, str) and value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        raise ApiError("Invalid date format. Use ISO 8601.", status_code=400)


@events_bp.post("/create")
@jwt_required()
@role_required("INSTITUTE")
def create_event():
    uid = int(current_user_id())
    institute = Institute.query.filter_by(user_id=uid).first()
    if not institute:
        raise ApiError("You must apply as an institute first", status_code=403)
    if institute.approval_status != "APPROVED":
        raise ApiError("Your institute is not approved yet", status_code=403)

    # Use request.form for multipart data
    data = request.form
    title = (data.get("title") or "").strip()
    if not title:
        raise ApiError("Title is required", status_code=400)

    date_str = data.get("date")
    if not date_str:
        raise ApiError("Date is required", status_code=400)
    event_date = _parse_iso_datetime(date_str)

    end_date_str = data.get("end_date")
    if not end_date_str:
        raise ApiError("End date is required", status_code=400)
    end_date = _parse_iso_datetime(end_date_str)

    if end_date <= event_date:
        raise ApiError("End date must be after start date", status_code=400)

    location = (data.get("location") or "").strip()
    if not location:
        raise ApiError("Location is required", status_code=400)

    def _to_int(v, default):
        try: return int(v or default)
        except: return default

    event = Event(
        institute_id=institute.id,
        title=title,
        description=data.get("description", ""),
        date=event_date,
        end_date=end_date,
        location=location,
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        extra_locations=data.get("extra_locations"),
        capacity=_to_int(data.get("capacity"), 100),
        num_rounds=_to_int(data.get("num_rounds"), 1),
        fees=_to_int(data.get("fees"), 0),
    )
    
    # Handle Image Upload
    if "image" in request.files:
        file = request.files["image"]
        if file and file.filename:
            import os
            import uuid
            from flask import current_app
            ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else "png"
            filename = f"{uuid.uuid4().hex}.{ext}"
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            event.image_url = f"/uploads/{filename}"
    
    db.session.add(event)
    db.session.flush()  # Populate event.id from DB
    
    # Handle initial announcement
    announcement = (data.get("announcement") or "").strip()
    if announcement:
        from models.event_update import EventUpdate
        update = EventUpdate(event_id=event.id, message=announcement)
        db.session.add(update)

    db.session.commit()
    return jsonify({"event": event.to_dict()}), 201


@events_bp.get("")
def list_events():
    """List all approved events."""
    events = Event.query.filter_by(approval_status="APPROVED").order_by(Event.date.asc()).all()
    return jsonify({"events": [e.to_dict() for e in events]}), 200


@events_bp.get("/all")
@jwt_required()
@role_required("INSTITUTE", "VOLUNTEER")
def list_my_events():
    """List events for the current institute or assigned to the volunteer."""
    uid = int(current_user_id())
    from models.user import User
    user = User.query.get(uid)
    
    if user.role == "VOLUNTEER":
        from models.volunteer import Volunteer
        vols = Volunteer.query.filter_by(user_id=uid).all()
        events = [v.event for v in vols if v.event]
        return jsonify({"events": [e.to_dict() for e in events]}), 200
        
    institute = Institute.query.filter_by(user_id=uid).first()
    if not institute:
        return jsonify({"events": []}), 200
    events = Event.query.filter_by(institute_id=institute.id).order_by(Event.created_at.desc()).all()
    return jsonify({"events": [e.to_dict() for e in events]}), 200


@events_bp.get("/<int:event_id>")
def get_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)
    
    e_dict = event.to_dict()
    # Group participants by round
    from models.participant import Participant
    parts = Participant.query.filter_by(event_id=event_id).all()
    
    # Only show PAID participants in the "Qualifiers" section
    qualifiers = {}
    for r in range(1, event.num_rounds + 1):
        qualifiers[r] = [p.to_dict() for p in parts if p.qualified_round >= r and p.payment_status == 'PAID']
    
    e_dict["qualifiers"] = qualifiers
    return jsonify({"event": e_dict}), 200
