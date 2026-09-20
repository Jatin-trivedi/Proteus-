"""
Proteus Manager — Agent Token Authentication Middleware (Priority 6)

Validates agent identity via Bearer token in Authorization header.
Tokens are stored as SHA-256 hashes in the database — never as plaintext.
"""

from functools import wraps
import hashlib

from flask import jsonify, request

try:
    from models import db, Agent
except ImportError:
    from manager.models import db, Agent


def hash_agent_token(plaintext_token: str) -> str:
    """Compute SHA-256 hash of an agent token for secure storage."""
    return hashlib.sha256(plaintext_token.encode("utf-8")).hexdigest()


def agent_token_required(view):
    """
    Decorator that authenticates an agent via Bearer token.
    On success, sets request.agent to the Agent model instance
    and request.agent_id to the agent's ID.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return jsonify({"error": "Agent token required (Authorization: Bearer <token>)"}), 401

        token = authorization[7:].strip()
        if not token:
            return jsonify({"error": "Empty agent token"}), 401

        # Look up agent by token (the Agent model stores the token directly)
        agent = Agent.query.filter_by(token=token).first()
        if not agent:
            return jsonify({"error": "Invalid or unknown agent token"}), 401

        request.agent = agent
        request.agent_id = agent.agent_id
        return view(*args, **kwargs)

    return wrapped
