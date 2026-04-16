from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from database.db import db
from models.institute import Institute
from models.event import Event
from models.leaderboard import Leaderboard
from services.errors import ApiError
from utils.decorators import role_required
from utils.jwt_handler import current_user_id


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/institutes/pending")
@jwt_required()
@role_required("ADMIN")
def pending_institutes():
    institutes = Institute.query.filter_by(approval_status="PENDING").order_by(Institute.created_at.desc()).all()
    return jsonify({"institutes": [i.to_dict() for i in institutes]}), 200


@admin_bp.get("/institutes/all")
@jwt_required()
@role_required("ADMIN")
def all_institutes():
    institutes = Institute.query.order_by(Institute.created_at.desc()).all()
    return jsonify({"institutes": [i.to_dict() for i in institutes]}), 200


@admin_bp.post("/institutes/approve/<int:institute_id>")
@jwt_required()
@role_required("ADMIN")
def approve_institute(institute_id):
    from models.institute import Institute
    institute = Institute.query.get(institute_id)
    if not institute:
        raise ApiError("Institute not found", status_code=404)

    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "APPROVED").strip().upper()
    reason = (data.get("reason") or f"Institute '{institute.name}' was {action.lower()}.").strip()
    
    if action not in ("APPROVED", "REJECTED"):
        raise ApiError("action must be APPROVED or REJECTED", status_code=400)

    institute.approval_status = action
    institute.admin_remarks = reason
    
    # Record Activity Log
    from models.activity_log import ActivityLog
    uid = int(current_user_id())
    log = ActivityLog(
        admin_id=uid,
        action_type=f"INSTITUTE_{action}",
        target_id=institute.id,
        target_name=institute.name,
        details=reason
    )
    db.session.add(log)

    # Notify the institute about their approval/rejection
    from models.notification import Notification
    notif = Notification(
        user_id=institute.user_id,
        title=f"Institute {action.title()}: {institute.name}",
        message=reason,
        type=f"INSTITUTE_{action}"
    )
    db.session.add(notif)
    
    db.session.commit()
    return jsonify({"institute": institute.to_dict(), "message": f"Institute {action.lower()} successfully"}), 200


@admin_bp.get("/events/pending")
@jwt_required()
@role_required("ADMIN")
def pending_events():
    events = Event.query.filter_by(approval_status="PENDING").order_by(Event.created_at.desc()).all()
    return jsonify({"events": [e.to_dict() for e in events]}), 200


@admin_bp.post("/events/approve/<int:event_id>")
@jwt_required()
@role_required("ADMIN")
def approve_event(event_id):
    from models.event import Event
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)

    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "APPROVED").strip().upper()
    reason = (data.get("reason") or f"Event '{event.title}' was {action.lower()}.").strip()

    if action not in ("APPROVED", "REJECTED"):
        raise ApiError("action must be APPROVED or REJECTED", status_code=400)

    event.approval_status = action
    event.admin_remarks = reason
    
    # Record Activity Log
    from models.activity_log import ActivityLog
    uid = int(current_user_id())
    log = ActivityLog(
        admin_id=uid,
        action_type=f"EVENT_{action}",
        target_id=event.id,
        target_name=event.title,
        details=reason
    )
    db.session.add(log)

    from models.user import User
    from models.notification import Notification

    # Notify the institute that owns this event
    inst_notif = Notification(
        user_id=event.institute.user_id,
        title=f"Event {action.title()}: {event.title}",
        message=reason,
        type=f"EVENT_{action}"
    )
    db.session.add(inst_notif)

    if action == "APPROVED":
        participants = User.query.filter_by(role="PARTICIPANT").all()
        for p in participants:
            notification = Notification(
                user_id=p.id,
                title="New Event Approved!",
                message=f"A new event '{event.title}' has been approved and is now open for registration.",
                type="EVENT_APPROVAL"
            )
            db.session.add(notification)

    db.session.commit()
    return jsonify({"event": event.to_dict()}), 200

@admin_bp.get("/events/all")
@jwt_required()
@role_required("ADMIN")
def all_events():
    events = Event.query.order_by(Event.created_at.desc()).all()
    return jsonify({"events": [e.to_dict() for e in events]}), 200

@admin_bp.delete("/events/<int:event_id>")
@jwt_required()
@role_required("ADMIN")
def delete_event(event_id):
    from models.event import Event
    from models.activity_log import ActivityLog
    
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)
        
    title = event.title
    uid = int(current_user_id())
    
    db.session.delete(event)
    
    log = ActivityLog(
        admin_id=uid,
        action_type="EVENT_DELETED",
        target_id=event_id,
        target_name=title,
        details=f"Event '{title}' was permanently deleted by admin."
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({"message": f"Event '{title}' has been successfully deleted."}), 200


@admin_bp.get("/participants/all")
@jwt_required()
@role_required("ADMIN")
def all_participants():
    from models.user import User
    users = User.query.filter_by(role="PARTICIPANT").order_by(User.created_at.desc()).all()
    return jsonify({"participants": [u.to_dict() for u in users]}), 200

@admin_bp.get("/stats")
@jwt_required()
@role_required("ADMIN")
def platform_stats():
    from models.user import User
    from models.participant import Participant

    from sqlalchemy import text
    from database.db import db
    
    total_users = db.session.execute(text("SELECT count(id) FROM users")).scalar() or 0
    total_institutes = db.session.execute(text("SELECT count(id) FROM institutes WHERE approval_status='APPROVED'")).scalar() or 0
    total_events = db.session.execute(text("SELECT count(id) FROM events WHERE approval_status='APPROVED'")).scalar() or 0
    total_participants = db.session.execute(text("SELECT count(id) FROM users WHERE role='PARTICIPANT'")).scalar() or 0
    pending_institutes = db.session.execute(text("SELECT count(id) FROM institutes WHERE approval_status='PENDING'")).scalar() or 0
    pending_events = db.session.execute(text("SELECT count(id) FROM events WHERE approval_status='PENDING'")).scalar() or 0

    return jsonify({
        "total_users": total_users,
        "total_institutes": total_institutes,
        "total_events": total_events,
        "total_participants": total_participants,
        "pending_institutes": pending_institutes,
        "pending_events": pending_events,
    }), 200


@admin_bp.post("/create-admin")
@jwt_required()
@role_required("ADMIN")
def create_admin():
    from services.auth_service import register_user
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    user, created = register_user(
        db=db,
        email=email,
        username=None,
        password=password,
        role="ADMIN",
        full_name=full_name,
        allow_admin_registration=True
    )
    if created:
        return jsonify({"message": "Admin created successfully", "admin": user.to_dict()}), 201
    return jsonify({"message": "Admin already exists", "admin": user.to_dict()}), 200
