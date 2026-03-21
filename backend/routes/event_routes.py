from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from database.db import db
from models.event import Event
from services.errors import ApiError
from services.event_service import (
    create_event,
    delete_event,
    get_event_or_404,
    list_events,
    organizer_events,
)
from utils.decorators import role_required
from utils.jwt_handler import current_user_id


events_bp = Blueprint("events", __name__, url_prefix="/events")


def _parse_uuid(value, field="id"):
    try:
        return UUID(str(value))
    except Exception:
        raise ApiError("Invalid id", status_code=400, details={"field": field})


@events_bp.get("")
def get_events():
    q = request.args.get("q")
    category = request.args.get("category")

    # Optional organizer dashboard: /events?mine=true (requires JWT)
    mine = (request.args.get("mine") or "").lower() == "true"
    if mine:
        # Soft-require JWT if mine=true; return 401 if missing.
        from flask_jwt_extended import verify_jwt_in_request

        verify_jwt_in_request()
        uid = current_user_id()
        role = (get_jwt().get("role") or "").upper()
        if role not in ("ORGANIZER", "ADMIN"):
            raise ApiError("Only organizers can list hosted events", status_code=403, error="forbidden")
        events = organizer_events(_parse_uuid(uid, field="user_id"))
        return jsonify({"events": [e.to_dict() for e in events]}), 200

    events = list_events(q=q, category=category)
    return jsonify({"events": [e.to_dict(include_organizer=True) for e in events]}), 200


@events_bp.get("/<event_id>")
def get_event(event_id):
    event = get_event_or_404(_parse_uuid(event_id))
    return jsonify({"event": event.to_dict(include_organizer=True)}), 200


@events_bp.post("")
@jwt_required()
@role_required("ADMIN", "ORGANIZER")
def post_event():
    payload = request.get_json(silent=True) or {}
    uid = _parse_uuid(current_user_id(), field="user_id")
    from models.user import User

    user = User.query.get(uid)
    if not user:
        raise ApiError("User not found", status_code=404, error="not_found")

    event = create_event(db=db, organizer_user=user, payload=payload)
    return jsonify({"event": event.to_dict(include_organizer=True)}), 201


@events_bp.put("/<event_id>")
@jwt_required()
def put_event(event_id):
    payload = request.get_json(silent=True) or {}
    event = get_event_or_404(_parse_uuid(event_id))

    uid = _parse_uuid(current_user_id(), field="user_id")
    from models.user import User
    from services.event_service import update_event

    user = User.query.get(uid)
    if not user:
        raise ApiError("User not found", status_code=404, error="not_found")

    event = update_event(db=db, event=event, actor_user=user, payload=payload)
    return jsonify({"event": event.to_dict(include_organizer=True)}), 200


@events_bp.delete("/<event_id>")
@jwt_required()
def delete_event_route(event_id):
    event = get_event_or_404(_parse_uuid(event_id))

    uid = _parse_uuid(current_user_id(), field="user_id")
    from models.user import User

    user = User.query.get(uid)
    if not user:
        raise ApiError("User not found", status_code=404, error="not_found")

    delete_event(db=db, event=event, actor_user=user)
    return jsonify({"deleted": True}), 200


@events_bp.delete("/<event_id>/force")
@jwt_required()
@role_required("ADMIN", "ORGANIZER")
def delete_event_force(event_id):
    """
    Hard delete an event even if it has bookings.
    Use with caution; intended for test cleanup.
    """
    from models.booking import Booking

    event = get_event_or_404(_parse_uuid(event_id))

    uid = _parse_uuid(current_user_id(), field="user_id")
    from models.user import User

    user = User.query.get(uid)
    if not user:
        raise ApiError("User not found", status_code=404, error="not_found")

    if user.role != "ADMIN" and event.organizer_id != user.user_id:
        raise ApiError("You can only delete your own events", status_code=403, error="forbidden")

    # Remove bookings first (and tickets via cascade).
    Booking.query.filter_by(event_id=event.event_id).delete()
    delete_event(db=db, event=event, actor_user=user)
    return jsonify({"deleted": True, "forced": True}), 200


@events_bp.get("/<event_id>/attendees")
@jwt_required()
@role_required("ADMIN", "ORGANIZER")
def get_attendees(event_id):
    event = get_event_or_404(_parse_uuid(event_id))

    uid = _parse_uuid(current_user_id(), field="user_id")
    from models.user import User
    from services.event_service import event_attendees

    user = User.query.get(uid)
    if not user:
        raise ApiError("User not found", status_code=404, error="not_found")

    if user.role != "ADMIN" and event.organizer_id != user.user_id:
        raise ApiError("You can only view attendees for your own events", status_code=403, error="forbidden")

    attendees = event_attendees(event)
    return jsonify({"event_id": str(event.event_id), "attendees": attendees}), 200
