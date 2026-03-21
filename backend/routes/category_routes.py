from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from database.db import db
from models.category import Category
from services.errors import ApiError
from utils.decorators import role_required


categories_bp = Blueprint("categories", __name__, url_prefix="/categories")


@categories_bp.get("")
def list_categories():
    categories = Category.query.order_by(Category.name.asc()).all()
    return jsonify({"categories": [c.to_dict() for c in categories]}), 200


@categories_bp.post("")
@jwt_required()
@role_required("ADMIN", "ORGANIZER")
def create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        raise ApiError("Category name is required", status_code=400, details={"field": "name"})

    existing = Category.query.filter_by(name=name).first()
    if existing:
        return jsonify({"category": existing.to_dict()}), 200

    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return jsonify({"category": category.to_dict()}), 201

