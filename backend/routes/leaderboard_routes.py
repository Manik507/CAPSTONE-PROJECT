from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from models.leaderboard import Leaderboard
from utils.jwt_handler import current_user_id


leaderboard_bp = Blueprint("leaderboard", __name__, url_prefix="/leaderboard")


@leaderboard_bp.get("/global")
def global_leaderboard():
    """Return global leaderboard sorted by XP (default) or trophies (?sort=trophies)."""
    sort = request.args.get("sort", "xp").lower()
    if sort == "trophies":
        entries = Leaderboard.query.order_by(Leaderboard.trophies.desc(), Leaderboard.xp.desc()).limit(100).all()
    else:
        entries = Leaderboard.query.order_by(Leaderboard.xp.desc(), Leaderboard.trophies.desc()).limit(100).all()
    return jsonify({"leaderboard": [e.to_dict() for e in entries]}), 200


@leaderboard_bp.get("/me")
@jwt_required()
def my_rank():
    uid = int(current_user_id())
    entry = Leaderboard.query.filter_by(user_id=uid).first()
    if not entry:
        return jsonify({"leaderboard": None, "message": "No leaderboard entry yet"}), 200
    return jsonify({"leaderboard": entry.to_dict()}), 200


@leaderboard_bp.get("/stats")
def public_stats():
    """Public endpoint: approved events, total participants, approved institutes."""
    from database.db import db
    from sqlalchemy import text

    approved_events = db.session.execute(text("SELECT count(id) FROM events WHERE approval_status='APPROVED'")).scalar() or 0
    approved_institutes = db.session.execute(text("SELECT count(id) FROM institutes WHERE approval_status='APPROVED'")).scalar() or 0
    total_participants = db.session.execute(text("SELECT count(id) FROM users WHERE role='PARTICIPANT'")).scalar() or 0

    return jsonify({
        "approved_events": approved_events,
        "total_participants": total_participants,
        "approved_institutes": approved_institutes,
    }), 200
