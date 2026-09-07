from functools import wraps
from flask import current_app, jsonify, request
import jwt


def jwt_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return jsonify({"error": "Authorization token required"}), 401
        try:
            claims = jwt.decode(
                authorization[7:],
                current_app.config["SECRET_KEY"],
                algorithms=[current_app.config["JWT_ALGORITHM"]],
            )
        except jwt.PyJWTError:
            return jsonify({"error": "Invalid or expired token"}), 401
        request.jwt_claims = claims
        return view(*args, **kwargs)

    return wrapped
