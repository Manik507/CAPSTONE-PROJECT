from sqlalchemy.exc import IntegrityError

from models.user import User
from services.errors import ApiError


ALLOWED_ROLES = {"ADMIN", "ORGANIZER", "ATTENDEE"}


def register_user(db, email, password, role, full_name, allow_admin_registration=False):
    email = (email or "").strip().lower()
    if not email or not password:
        raise ApiError("Email and password are required", status_code=400)

    role = (role or "ATTENDEE").strip().upper()
    if role not in ALLOWED_ROLES:
        raise ApiError("Invalid role", status_code=400, details={"allowed_roles": sorted(ALLOWED_ROLES)})

    if role == "ADMIN" and not allow_admin_registration:
        raise ApiError("Admin registration is disabled", status_code=403)

    existing = User.query.filter_by(email=email).first()
    if existing:
        # Allow idempotent registration when password matches.
        if existing.check_password(password):
            return existing, False
        raise ApiError(
            "Email already registered",
            status_code=409,
            error="conflict",
            details={"email": email},
        )

    full_name = (full_name or "").strip()
    if not full_name:
        raise ApiError("Full name is required", status_code=400, details={"field": "full_name"})

    user = User(email=email, role=role, full_name=full_name)
    user.set_password(password)

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError(
            "Email already registered",
            status_code=409,
            error="conflict",
            details={"email": email},
        )

    return user, True


def authenticate_user(db, email, password):
    email = (email or "").strip().lower()
    if not email or not password:
        raise ApiError("Email and password are required", status_code=400)

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise ApiError("Invalid credentials", status_code=401, error="unauthorized")
    return user
