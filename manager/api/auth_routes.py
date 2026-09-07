from datetime import datetime, timedelta, timezone
from flask import Blueprint, current_app, jsonify, request
import jwt
from models import db, User
from middleware.auth import jwt_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


def create_token(user):
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": user.user_id,
        "username": user.username,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(seconds=current_app.config["JWT_EXPIRATION"]),
    }, current_app.config["SECRET_KEY"], algorithm=current_app.config["JWT_ALGORITHM"])


@auth_bp.post("/register")
def register():
    data = request.get_json()
    if not isinstance(data, dict) or not data.get("username") or not data.get("password"):
        return jsonify({"error": "username and password required"}), 400
    if len(data["password"]) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "username already exists"}), 409
    user = User(username=data["username"], role=data.get("role", "analyst"))
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return jsonify({"user": user.to_dict(), "access_token": create_token(user)}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json()
    if not isinstance(data, dict) or not data.get("username") or not data.get("password"):
        return jsonify({"error": "username and password required"}), 400
    user = User.query.filter_by(username=data["username"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "invalid credentials"}), 401
    return jsonify({"user": user.to_dict(), "access_token": create_token(user)}), 200


@auth_bp.get("/me")
@jwt_required
def me():
    user = User.query.get(request.jwt_claims["sub"])
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200
