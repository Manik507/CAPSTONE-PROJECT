from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from database.db import db
from models.user import User
from models.follow import Follow
from models.leaderboard import Leaderboard
from models.institute import Institute
from models.participant import Participant
from models.event_result import EventResult
from models.reward_history import RewardHistory
from models.event import Event
from models.activity_log import ActivityLog
from services.errors import ApiError
from utils.decorators import role_required
from utils.jwt_handler import current_user_id

social_bp = Blueprint("social", __name__)


@social_bp.get("/social/search")
@jwt_required()
def search_users():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"users": []}), 200

    # Search in User.username or Institute.name
    # We join with Institute (outer join) to includes users who are not institutes
    users = User.query.outerjoin(Institute).filter(
        (User.username.ilike(f"%{query}%")) | (Institute.name.ilike(f"%{query}%")) | (User.full_name.ilike(f"%{query}%"))
    ).limit(20).all()

    uid = int(current_user_id())
    # Identify who we are already following
    following_ids = [f.followed_id for f in Follow.query.filter_by(follower_id=uid).all()]

    results = []
    for u in users:
        if u.id == uid:
            continue
        
        u_dict = u.to_dict()
        u_dict["is_following"] = u.id in following_ids
        results.append(u_dict)

    return jsonify({"users": results}), 200


@social_bp.post("/social/follow/<int:user_id>")
@jwt_required()
def follow_user(user_id):
    uid = int(current_user_id())
    if uid == user_id:
        raise ApiError("You cannot follow yourself", status_code=400)

    target = User.query.get(user_id)
    if not target:
        raise ApiError("User not found", status_code=404)

    existing = Follow.query.filter_by(follower_id=uid, followed_id=user_id).first()
    if existing:
        return jsonify({"message": "Already following"}), 200

    follow = Follow(follower_id=uid, followed_id=user_id)
    db.session.add(follow)
    db.session.commit()
    return jsonify({"message": f"You are now following {target.username}"}), 201


@social_bp.post("/social/unfollow/<int:user_id>")
@jwt_required()
def unfollow_user(user_id):
    uid = int(current_user_id())
    follow = Follow.query.filter_by(follower_id=uid, followed_id=user_id).first()
    if not follow:
        return jsonify({"message": "Not following"}), 200

    db.session.delete(follow)
    db.session.commit()
    return jsonify({"message": "Unfollowed successfully"}), 200


@social_bp.get("/social/profile/<int:user_id>")
@jwt_required()
def get_user_profile(user_id):
    u = User.query.get(user_id)
    if not u:
        raise ApiError("User not found", status_code=404)

    uid = int(current_user_id())
    
    # Base profile info
    requester = User.query.get(uid)
    requester_role = requester.role if requester else "PARTICIPANT"

    res = {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "role": u.role,
        "email": u.email if u.role != "ADMIN" or requester_role in ["INSTITUTE", "ADMIN"] else "Private", 
        "phone": (u.phone_number if u.role != "ADMIN" or requester_role in ["INSTITUTE", "ADMIN"] else "Private") if hasattr(u, 'phone_number') else "N/A",
        "follower_count": Follow.query.filter_by(followed_id=user_id).count(),
        "following_count": Follow.query.filter_by(follower_id=user_id).count(),
    }

    if u.role == "INSTITUTE":
        inst = Institute.query.filter_by(user_id=user_id).first()
        if inst:
            res["full_name"] = inst.name
            res["email"] = inst.email # Use official institute email

    # Show XP/Trophies only for participants
    if u.role == "PARTICIPANT":
        # Leaderboard stats
        lb = Leaderboard.query.filter_by(user_id=user_id).first()
        res["xp"] = lb.xp if lb else 0
        res["trophies"] = lb.trophies if lb else 0
    else:
        res["xp"] = 0
        res["trophies"] = 0

    # Mutual Connections: Users that BOTH current_user and target_user are FOLLOWING
    my_following_ids = [f.followed_id for f in Follow.query.filter_by(follower_id=uid).all()]
    their_following_ids = [f.followed_id for f in Follow.query.filter_by(follower_id=user_id).all()]
    mutual_ids_set = set(my_following_ids).intersection(set(their_following_ids))
    mutual_ids = list(mutual_ids_set)
    
    mutual_users = User.query.filter(User.id.in_(mutual_ids)).all() if mutual_ids else []
    res["mutual_connections"] = [
        {"id": mu.id, "username": mu.username, "full_name": mu.full_name} 
        for mu in mutual_users
    ]

    # Current user follow status
    res["is_following"] = user_id in my_following_ids

    # Competition History (Public)
    history = []
    try:
        if u.role == "PARTICIPANT":
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            
            parts = Participant.query.filter_by(user_id=user_id).all()
            for p in parts:
                if not p.event: continue
                # ONLY show in history if the event has ENDED
                if p.event.end_date and p.event.end_date > now:
                    continue
                
                res_entry = EventResult.query.filter_by(user_id=user_id, event_id=p.event_id).first()
                rws = RewardHistory.query.filter_by(user_id=user_id, event_id=p.event_id).all()
                
                history.append({
                    "event_title": p.event.title,
                    "event_date": p.event.date.isoformat() if p.event.date else None,
                    "institute_description": p.event.description,
                    "prize": res_entry.prize_name if res_entry else None,
                    "rewards": {
                        "xp": sum((r.xp_awarded or 0) for r in rws),
                        "trophies": sum((r.trophies_awarded or 0) for r in rws)
                    }
                })
        elif u.role == "VOLUNTEER":
            from models.volunteer import Volunteer
            # For volunteers, show only events they were assigned to
            vols = Volunteer.query.filter_by(user_id=user_id).all()
            for v in vols:
                if not v.event: continue
                history.append({
                    "event_title": v.event.title,
                    "event_date": v.event.date.isoformat() if v.event.date else None,
                    "institute_description": v.event.description,
                    "prize": "Volunteer",
                    "rewards": {"xp": 0, "trophies": 0}
                })
        elif u.role == "INSTITUTE":
            inst = Institute.query.filter_by(user_id=user_id).first()
            if inst:
                # For organizers, show only THEIR events that ARE APPROVED
                events = Event.query.filter_by(institute_id=inst.id, approval_status='APPROVED').all()
                for e in events:
                    history.append({
                        "event_title": e.title,
                        "event_date": e.date.isoformat() if e.date else None,
                        "institute_description": e.description,
                        "prize": None,
                        "rewards": {"xp": 0, "trophies": 0}
                    })
        elif u.role == "ADMIN":
            logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).all()
            for log in logs:
                admin_name = log.admin.full_name if log.admin else "Unknown Admin"
                history.append({
                    "event_title": f"{log.action_type}: {log.target_name}",
                    "event_date": log.created_at.isoformat() if log.created_at else None,
                    "institute_description": log.details or f"Action performed on {log.target_name}",
                    "prize": f"By {admin_name}", # Label for the UI
                    "rewards": {"xp": 0, "trophies": 0},
                    "target_id": log.target_id,
                    "target_type": "EVENT" if "EVENT" in log.action_type else "INSTITUTE",
                    "admin_name": admin_name
                })
    except Exception as e:
        # Don't crash the whole profile if history fails, just log it
        print(f"History fetch error for user {user_id}: {str(e)}")
        
    res["competition_history"] = history
    return jsonify({"profile": res}), 200


@social_bp.get("/social/followers/<int:user_id>")
@jwt_required()
def get_followers(user_id):
    followers = Follow.query.filter_by(followed_id=user_id).all()
    # Join with users table manually or use relationship if defined
    # We'll just fetch user details
    res = []
    for f in followers:
        u = User.query.get(f.follower_id)
        if u:
            u_data = u.to_dict()
            res.append({
                "id": u_data["id"], 
                "username": u_data["username"], 
                "full_name": u_data["full_name"], 
                "role": u_data["role"]
            })
    return jsonify({"followers": res}), 200


@social_bp.get("/social/following/<int:user_id>")
@jwt_required()
def get_following(user_id):
    following = Follow.query.filter_by(follower_id=user_id).all()
    res = []
    for f in following:
        u = User.query.get(f.followed_id)
        if u:
            u_data = u.to_dict()
            res.append({
                "id": u_data["id"], 
                "username": u_data["username"], 
                "full_name": u_data["full_name"], 
                "role": u_data["role"]
            })
    return jsonify({"following": res}), 200
