from flask import Blueprint, current_app, jsonify, request

from database.db import db
from services.auth_service import authenticate_user, register_user
from utils.jwt_handler import create_access_token_for_user


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    user, created = register_user(
        db=db,
        email=data.get("email"),
        password=data.get("password"),
        role=data.get("role"),
        full_name=data.get("full_name"),
        allow_admin_registration=current_app.config.get("ALLOW_ADMIN_REGISTRATION", False),
    )
    token = create_access_token_for_user(user)
    status = 201 if created else 200
    return jsonify({"user": user.to_public_dict(), "access_token": token, "created": created}), status


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user = authenticate_user(db=db, email=data.get("email"), password=data.get("password"))
    token = create_access_token_for_user(user)
    return jsonify({"user": user.to_public_dict(), "access_token": token}), 200
