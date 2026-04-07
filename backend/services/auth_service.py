from sqlalchemy.exc import IntegrityError

from models.user import User
from services.errors import ApiError


ALLOWED_ROLES = {"ADMIN", "INSTITUTE", "PARTICIPANT", "VOLUNTEER"}


def register_user(db, email, username, password, role, full_name, phone_number=None, allow_admin_registration=False):
    email = (email or "").strip().lower()
    if not email or not password:
        raise ApiError("Email and password are required", status_code=400)

    username = (username or "").strip().lower()
    if not username:
        # Default to email slug if not provided
        username = email.split('@')[0]
    
    # Check if username exists
    existing_un = User.query.filter_by(username=username).first()
    if existing_un:
        raise ApiError("User with this username already exists.", status_code=409)

    role = (role or "PARTICIPANT").strip().upper()
    if role not in ALLOWED_ROLES:
        raise ApiError("Invalid role", status_code=400, details={"allowed_roles": sorted(ALLOWED_ROLES)})

    if role == "ADMIN" and not allow_admin_registration:
        raise ApiError("Admin registration is disabled", status_code=403)

    existing = User.query.filter_by(email=email).first()
    if existing:
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
        
    phone_number = (phone_number or "").strip()
    if role == "PARTICIPANT":
        if not phone_number or len(phone_number) != 10:
            raise ApiError("A valid 10-digit phone number is required for participants", status_code=400)
    elif phone_number and len(phone_number) < 10:
        # For non-participants, if they provide one, make it 10
        raise ApiError("Phone number must be at least 10 digits", status_code=400)

    user = User(email=email, username=username, role=role, full_name=full_name, phone_number=phone_number)
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
