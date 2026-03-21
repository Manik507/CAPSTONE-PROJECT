from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from database.db import db
from services.booking_service import cancel_booking, create_booking, list_user_bookings
from services.errors import ApiError
from utils.decorators import role_required
from utils.jwt_handler import current_user_id


bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


def _parse_uuid(value, field="id"):
    try:
        return UUID(str(value))
    except Exception:
        raise ApiError("Invalid id", status_code=400, details={"field": field})


@bookings_bp.post("")
@jwt_required()
@role_required("ADMIN", "ATTENDEE")
def book_event():
    data = request.get_json(silent=True) or {}
    event_id = data.get("event_id")
    if not event_id:
        raise ApiError("event_id is required", status_code=400, details={"field": "event_id"})

    uid = _parse_uuid(current_user_id(), field="user_id")
    from models.user import User

    user = User.query.get(uid)
    if not user:
        raise ApiError("User not found", status_code=404, error="not_found")

    booking, ticket = create_booking(db=db, user=user, event_id=_parse_uuid(event_id, field="event_id"))
    return jsonify({"booking": booking.to_dict(include_event=True), "ticket": ticket.to_dict()}), 201


@bookings_bp.get("/user")
@jwt_required()
def my_bookings():
    uid = _parse_uuid(current_user_id(), field="user_id")
    role = (get_jwt().get("role") or "").upper()
    if role not in ("ATTENDEE", "ADMIN"):
        raise ApiError("Only attendees can view booked events", status_code=403, error="forbidden")

    bookings = list_user_bookings(uid)
    return jsonify({"bookings": [b.to_dict(include_event=True) for b in bookings]}), 200


@bookings_bp.delete("/<booking_id>")
@jwt_required()
def cancel(booking_id):
    uid = _parse_uuid(current_user_id(), field="user_id")
    from models.user import User

    user = User.query.get(uid)
    if not user:
        raise ApiError("User not found", status_code=404, error="not_found")

    booking = cancel_booking(db=db, booking_id=_parse_uuid(booking_id), actor_user=user)
    return jsonify({"booking": booking.to_dict(include_event=True)}), 200
