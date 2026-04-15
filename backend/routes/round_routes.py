"""
Round Qualification Module — Separate from participants as per spec.

Provides read-only endpoints for viewing round status and participants
per round. The actual locking is done via the qualify endpoint in
institute_routes.py (POST /institutes/events/<event_id>/qualify).
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from database.db import db
from models.event import Event
from models.participant import Participant
from models.round_lock import RoundLock
from services.errors import ApiError
from utils.decorators import role_required
from utils.jwt_handler import current_user_id


rounds_bp = Blueprint("rounds", __name__, url_prefix="/rounds")


@rounds_bp.get("/<int:event_id>/status")
@jwt_required()
@role_required("INSTITUTE", "ADMIN", "VOLUNTEER")
def round_status(event_id):
    """
    Get the lock status for every round of an event.
    Returns which rounds are locked, participant counts, and whether
    the next round can be locked.
    """
    from models.user import User
    from models.institute import Institute
    from models.volunteer import Volunteer

    uid = int(current_user_id())
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)

    # Access control
    user = User.query.get(uid)
    if user.role == "VOLUNTEER":
        v = Volunteer.query.filter_by(user_id=uid, event_id=event_id).first()
        if not v:
            raise ApiError("Not authorized for this event", status_code=403)
    elif user.role == "INSTITUTE":
        institute = Institute.query.filter_by(user_id=uid).first()
        if not institute or event.institute_id != institute.id:
            raise ApiError("Not authorized for this event", status_code=403)

    # Gather lock info
    locks = RoundLock.query.filter_by(event_id=event_id).order_by(RoundLock.round_number.asc()).all()
    locked_rounds = {lock.round_number: lock.to_dict() for lock in locks}

    rounds_info = []
    for r in range(1, event.num_rounds + 1):
        # Count participants qualified for this round
        if r == 1:
            count = Participant.query.filter_by(
                event_id=event_id, payment_status="PAID"
            ).count()
        else:
            count = Participant.query.filter_by(
                event_id=event_id, payment_status="PAID"
            ).filter(
                Participant.qualified_round >= r
            ).count()

        # A round can be locked if: it's not already locked AND all previous rounds are locked
        can_lock = (r not in locked_rounds) and all(
            prev in locked_rounds for prev in range(1, r)
        )

        rounds_info.append({
            "round_number": r,
            "is_locked": r in locked_rounds,
            "lock_info": locked_rounds.get(r),
            "participant_count": count,
            "can_lock": can_lock,
        })

    # Determine next round available for locking
    next_lockable = None
    for info in rounds_info:
        if not info["is_locked"] and info["can_lock"]:
            next_lockable = info["round_number"]
            break

    return jsonify({
        "event_id": event_id,
        "num_rounds": event.num_rounds,
        "rounds": rounds_info,
        "next_lockable_round": next_lockable,
        "all_rounds_locked": all(info["is_locked"] for info in rounds_info),
        "results_locked": event.results_locked,
    }), 200


@rounds_bp.get("/<int:event_id>/<int:round_number>/participants")
@jwt_required()
@role_required("INSTITUTE", "ADMIN", "VOLUNTEER")
def round_participants(event_id, round_number):
    """Get participants who qualified for a specific round."""
    from models.user import User
    from models.institute import Institute
    from models.volunteer import Volunteer

    uid = int(current_user_id())
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)

    if round_number < 1 or round_number > event.num_rounds:
        raise ApiError(f"Round must be between 1 and {event.num_rounds}", status_code=400)

    # Access control
    user = User.query.get(uid)
    if user.role == "VOLUNTEER":
        v = Volunteer.query.filter_by(user_id=uid, event_id=event_id).first()
        if not v:
            raise ApiError("Not authorized for this event", status_code=403)
    elif user.role == "INSTITUTE":
        institute = Institute.query.filter_by(user_id=uid).first()
        if not institute or event.institute_id != institute.id:
            raise ApiError("Not authorized for this event", status_code=403)

    # Get participants for this round
    if round_number == 1:
        participants = Participant.query.filter_by(
            event_id=event_id, payment_status="PAID"
        ).all()
    else:
        participants = Participant.query.filter_by(
            event_id=event_id, payment_status="PAID"
        ).filter(
            Participant.qualified_round >= round_number
        ).all()

    lock = RoundLock.query.filter_by(event_id=event_id, round_number=round_number).first()

    return jsonify({
        "event_id": event_id,
        "round_number": round_number,
        "is_locked": lock is not None,
        "lock_info": lock.to_dict() if lock else None,
        "participants": [p.to_dict() for p in participants],
    }), 200
