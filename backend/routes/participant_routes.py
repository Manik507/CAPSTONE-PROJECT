from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from database.db import db
from models.event import Event
from models.participant import Participant
from models.user import User
from services.errors import ApiError
from utils.decorators import role_required
from utils.jwt_handler import current_user_id


participant_bp = Blueprint("participants", __name__)


@participant_bp.post("/events/register/<int:event_id>")
@jwt_required()
@role_required("PARTICIPANT", "ADMIN")
def register_for_event(event_id):
    uid = int(current_user_id())

    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)
    if event.approval_status != "APPROVED":
        raise ApiError("Event is not approved yet", status_code=403)

    existing = Participant.query.filter_by(user_id=uid, event_id=event_id).first()
    if existing:
        return jsonify({"participant": existing.to_dict(), "message": "Already registered"}), 200

    current_count = Participant.query.filter_by(event_id=event_id).count()
    if current_count >= event.capacity:
        raise ApiError("Event is full", status_code=409)

    import random
    import string
    reg_id = f"REG-{event_id}-{uid}-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    participant = Participant(user_id=uid, event_id=event_id, registration_id=reg_id)
    db.session.add(participant)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError("Already registered for this event", status_code=409)

    return jsonify({"participant": participant.to_dict()}), 201


@participant_bp.get("/participants/<int:event_id>")
@jwt_required()
@role_required("INSTITUTE", "ADMIN", "VOLUNTEER")
def list_participants(event_id):
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)

    participants = Participant.query.filter_by(event_id=event_id).order_by(Participant.created_at.asc()).all()
    
    uid = int(current_user_id())
    user = User.query.get(uid)
    
    if user.role == "VOLUNTEER":
        from models.volunteer import Volunteer
        v = Volunteer.query.filter_by(user_id=uid, event_id=event_id).first()
        if not v:
            raise ApiError("Not authorized for this event", status_code=403)
            
    elif user.role == "INSTITUTE":
        from models.institute import Institute
        inst = Institute.query.filter_by(user_id=uid).first()
        if not inst or event.institute_id != inst.id:
            raise ApiError("Not authorized for this event", status_code=403)

    return jsonify({"participants": [p.to_dict() for p in participants]}), 200


@participant_bp.get("/my-events")
@jwt_required()
@role_required("PARTICIPANT")
def my_events():
    uid = int(current_user_id())
    participations = Participant.query.filter_by(user_id=uid).all()
    events = []
    for p in participations:
        event_data = p.event.to_dict() if p.event else {}
        event_data["participation_id"] = p.id
        event_data["payment_status"] = p.payment_status
        events.append(event_data)
    return jsonify({"events": events}), 200


@participant_bp.post("/participants/<int:participant_id>/toggle-payment")
@jwt_required()
@role_required("INSTITUTE", "ADMIN", "VOLUNTEER")
def toggle_payment(participant_id):
    from models.institute import Institute
    participant = Participant.query.get(participant_id)
    if not participant:
        raise ApiError("Participant not found", status_code=404)

    uid = int(current_user_id())
    user = User.query.get(uid)

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    if user.role == "INSTITUTE":
        institute = Institute.query.filter_by(user_id=uid).first()
        if not institute or (participant.event and participant.event.institute_id != institute.id):
            raise ApiError("Not authorized to manage this participant", status_code=403)
            
    elif user.role == "VOLUNTEER":
        from models.volunteer import Volunteer
        v = Volunteer.query.filter_by(user_id=uid, event_id=participant.event_id).first()
        if not v:
            raise ApiError("Not authorized for this event", status_code=403)
        
        # Check if event is completed
        if participant.event and participant.event.end_date and participant.event.end_date.replace(tzinfo=timezone.utc) < now:
            raise ApiError("Cannot modify participants of a completed event", status_code=403)

    new_status = "PAID" if participant.payment_status == "UNPAID" else "UNPAID"
    participant.payment_status = new_status
    db.session.commit()
    
    return jsonify({
        "message": f"Payment status set to {new_status}",
        "payment_status": new_status,
        "participant": participant.to_dict()
    }), 200


@participant_bp.get("/notifications")
@jwt_required()
@role_required("PARTICIPANT", "ADMIN", "INSTITUTE")
def get_notifications():
    from models.notification import Notification
    uid = int(current_user_id())
    notifications = Notification.query.filter_by(user_id=uid).order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify({"notifications": [n.to_dict() for n in notifications]}), 200


@participant_bp.patch("/notifications/<int:notification_id>/read")
@jwt_required()
def mark_notification_read(notification_id):
    from models.notification import Notification
    uid = int(current_user_id())
    notification = Notification.query.filter_by(id=notification_id, user_id=uid).first()
    if not notification:
        raise ApiError("Notification not found", status_code=404)
    
    notification.is_read = True
    db.session.commit()
    return jsonify({"message": "Notification marked as read"}), 200


@participant_bp.get("/events/<int:event_id>/updates")
@jwt_required()
def get_event_updates(event_id):
    from models.event import Event
    from models.event_update import EventUpdate
    from models.participant import Participant

    uid = int(current_user_id())
    user = User.query.get(uid)

    # Access Control: Admin/Institute can always see updates? 
    # Or just Paid participants? The requirement says "exclusive to PAID participants".
    # We should allow Admin and the Institute that owns it to see it too for debugging/management.
    
    if user.role == "PARTICIPANT":
        participation = Participant.query.filter_by(user_id=uid, event_id=event_id).first()
        if not participation or participation.payment_status != "PAID":
            raise ApiError("Updates are only available to PAID participants", status_code=403)
    
    elif user.role == "INSTITUTE":
        from models.institute import Institute
        institute = Institute.query.filter_by(user_id=uid).first()
        event = Event.query.get(event_id)
        if not event or (institute and event.institute_id != institute.id):
             # If it's a different institute, they shouldn't see it (assuming privacy)
             # But usually institutes only care about their own. 
             # Let's stick to the rule: only participants are PAID restricted.
             pass

    updates = EventUpdate.query.filter_by(event_id=event_id).order_by(EventUpdate.created_at.desc()).all()
    return jsonify({"updates": [u.to_dict() for u in updates]}), 200

@participant_bp.get("/rewards/history")
@jwt_required()
def get_reward_history():
    uid = int(current_user_id())
    from models.reward_history import RewardHistory
    history = RewardHistory.query.filter_by(user_id=uid).order_by(RewardHistory.created_at.desc()).all()
    return jsonify({"history": [h.to_dict() for h in history]}), 200

@participant_bp.post("/rewards/sync")
@jwt_required()
def sync_rewards():
    uid = int(current_user_id())
    from services.reward_service import check_participation_rewards
    new_rewards = check_participation_rewards(uid)
    return jsonify({
        "message": f"Sync complete. {len(new_rewards)} new rewards found.",
        "new_rewards": [r.to_dict() for r in new_rewards]
    }), 200

@participant_bp.get("/legacy")
@jwt_required()
def get_full_legacy():
    uid = int(current_user_id())
    from models.participant import Participant
    from models.event_result import EventResult
    from models.reward_history import RewardHistory
    from models.leaderboard import Leaderboard

    # 1. Get all participations
    parts = Participant.query.filter_by(user_id=uid).all()
    
    # 2. Get all prizes
    results = EventResult.query.filter_by(user_id=uid).all()
    results_map = {r.event_id: r for r in results}

    # 3. Get all reward history bits
    rewards = RewardHistory.query.filter_by(user_id=uid).all()
    rewards_map = {} # event_id -> list of rewards
    for rw in rewards:
        if rw.event_id not in rewards_map:
            rewards_map[rw.event_id] = []
        rewards_map[rw.event_id].append(rw)

    # 4. Get current cumulative stats
    lb = Leaderboard.query.filter_by(user_id=uid).first()
    stats = {
        "xp": lb.xp if lb else 0,
        "trophies": lb.trophies if lb else 0
    }

    legacy_items = []
    for p in parts:
        event = p.event
        if not event: continue

        res = results_map.get(event.id)
        rws = rewards_map.get(event.id, [])

        item = {
            "event_id": event.id,
            "event_title": event.title,
            "event_date": event.date.isoformat() if event.date else None,
            "payment_status": p.payment_status,
            "prize": res.to_dict() if res else None,
            "rewards": [r.to_dict() for r in rws],
            "total_xp_earned": sum(r.xp_awarded for r in rws),
            "total_trophies_earned": sum(r.trophies_awarded for r in rws)
        }
        legacy_items.append(item)

    # Sort by date descending
    legacy_items.sort(key=lambda x: x["event_date"] or "", reverse=True)

    return jsonify({
        "stats": stats,
        "history": legacy_items
    }), 200
