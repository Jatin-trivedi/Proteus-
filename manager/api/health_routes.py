from flask import Blueprint, jsonify
from models import db
from datetime import datetime
import sys
import os

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health_check():
    """Production health check endpoint"""
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "connected",
            "api": "running"
        }
    }
    
    # Check database
    try:
        db.session.execute("SELECT 1")
    except Exception as e:
        status["status"] = "unhealthy"
        status["services"]["database"] = str(e)
    
    return jsonify(status), 200 if status["status"] == "healthy" else 503

@health_bp.route("/health/ready", methods=["GET"])
def readiness_check():
    """Kubernetes readiness probe"""
    return jsonify({"status": "ready"}), 200

@health_bp.route("/health/live", methods=["GET"])
def liveness_check():
    """Kubernetes liveness probe"""
    return jsonify({"status": "alive"}), 200