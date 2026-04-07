from functools import wraps
<<<<<<< HEAD

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

=======
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in roles:
                return jsonify({"error": "forbidden", "message": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
>>>>>>> temp-fix
