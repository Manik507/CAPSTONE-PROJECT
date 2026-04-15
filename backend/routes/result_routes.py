from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from database.db import db
from models.event import Event
from models.event_result import EventResult
from models.institute import Institute
from models.participant import Participant
from models.user import User
from services.errors import ApiError
from utils.decorators import role_required
from utils.jwt_handler import current_user_id

results_bp = Blueprint("results", __name__)

@results_bp.get("/results/event/<int:event_id>")
def get_event_results(event_id):
    """Public: Get the Hall of Fame for an event."""
    results = EventResult.query.filter_by(event_id=event_id).order_by(EventResult.rank.asc()).all()
    return jsonify({"results": [r.to_dict() for r in results]}), 200

@results_bp.post("/results/event/<int:event_id>")
@jwt_required()
@role_required("INSTITUTE", "ADMIN")
def set_event_results(event_id):
    """Institute: Set the winners for an event (3-Step Workflow Finalization).
    
    Once results are declared, they are permanently locked and cannot be changed.
    """
    uid = int(current_user_id())
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)

    # --- Results immutability check ---
    if event.results_locked:
        raise ApiError(
            "Results for this event have already been declared and are permanently locked. "
            "No changes are allowed.",
            status_code=409
        )

    # Check ownership
    user = User.query.get(uid)
    if user.role == "INSTITUTE":
        institute = Institute.query.filter_by(user_id=uid).first()
        if not institute or event.institute_id != institute.id:
            raise ApiError("Not authorized to manage results for this event", status_code=403)

    data = request.get_json(silent=True) or {}
    winners = data.get("winners") # Expected: list of {user_id, rank, prize_name, prize_description}
    if not isinstance(winners, list):
        raise ApiError("Winners list is required", status_code=400)

    # Clear any draft results (safety net — normally none exist since we lock after first declaration)
    EventResult.query.filter_by(event_id=event_id).delete()

    # Create new results
    winner_uids = []
    for w in winners:
        user_id = w.get("user_id")
        if not user_id: continue
        
        # Verify user is a participant
        p = Participant.query.filter_by(event_id=event_id, user_id=user_id).first()
        if not p: continue

        res = EventResult(
            event_id=event_id,
            user_id=user_id,
            rank=int(w.get("rank", 1)),
            prize_name=w.get("prize_name", "Winner"),
            prize_description=w.get("prize_description", "")
        )
        db.session.add(res)
        winner_uids.append(user_id)

    # Award XP and Trophies to ALL participants (Winners: 100XP+1T, Others: 50XP+0T)
    from services.reward_service import award_finalization_rewards
    award_finalization_rewards(event_id, winner_uids)

    # --- Lock results permanently ---
    event.results_locked = True

    db.session.commit()
    return jsonify({
        "message": "Event results finalized and permanently locked.",
        "results_locked": True,
        "results": [r.to_dict() for r in EventResult.query.filter_by(event_id=event_id).all()]
    }), 200
