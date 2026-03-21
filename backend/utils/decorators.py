from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def role_required(*allowed_roles):
    """
    Enforce role-based access control.

    Usage:
        @jwt_required()
        @role_required("ADMIN", "ORGANIZER")
        def handler(): ...
    """

    allowed = {r.upper() for r in allowed_roles}

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = (claims.get("role") or "").upper()
            if role not in allowed:
                return jsonify({"error": "forbidden", "message": "Insufficient permissions"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator

