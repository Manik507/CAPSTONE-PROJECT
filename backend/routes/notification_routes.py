from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from database.db import db
from models.notification import Notification
from services.errors import ApiError
from utils.jwt_handler import current_user_id


notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


def _parse_uuid(value, field="id"):
    try:
        return UUID(str(value))
    except Exception:
        raise ApiError("Invalid id", status_code=400, details={"field": field})


@notifications_bp.get("")
@jwt_required()
def list_notifications():
    uid = _parse_uuid(current_user_id(), field="user_id")
    notifications = (
        Notification.query.filter_by(user_id=uid)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return jsonify({"notifications": [n.to_dict() for n in notifications]}), 200


@notifications_bp.post("")
@jwt_required()
def create_notification():
    uid = _parse_uuid(current_user_id(), field="user_id")
    data = request.get_json(silent=True) or {}

    title = (data.get("title") or "").strip()
    message = (data.get("message") or "").strip()
    if not title or not message:
        raise ApiError("title and message are required", status_code=400)

    # Allow admins/organizers to target any user; otherwise only self
    target_id = data.get("user_id") or uid
    target_id = _parse_uuid(target_id, field="user_id")

    from models.user import User
    from flask_jwt_extended import get_jwt

    role = (get_jwt().get("role") or "").upper()
    if role not in ("ADMIN", "ORGANIZER") and target_id != uid:
        raise ApiError("You can only create notifications for yourself", status_code=403, error="forbidden")

    user = User.query.get(target_id)
    if not user:
        raise ApiError("User not found", status_code=404, error="not_found")

    notification = Notification(user_id=target_id, title=title, message=message)
    db.session.add(notification)
    db.session.commit()
    return jsonify({"notification": notification.to_dict()}), 201


@notifications_bp.put("/<notification_id>/read")
@jwt_required()
def mark_read(notification_id):
    uid = _parse_uuid(current_user_id(), field="user_id")
    nid = _parse_uuid(notification_id, field="notification_id")

    notification = Notification.query.get(nid)
    if not notification:
        raise ApiError("Notification not found", status_code=404, error="not_found")
    if notification.user_id != uid:
        raise ApiError("You can only update your own notifications", status_code=403, error="forbidden")

    notification.is_read = True
    db.session.commit()
    return jsonify({"notification": notification.to_dict()}), 200
