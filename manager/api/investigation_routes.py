"""
Proteus Manager — Investigation API Routes (Priority 7)

Endpoints for creating and querying forensic investigations.
"""

from flask import Blueprint, request, jsonify
import uuid
from datetime import datetime, timezone

try:
    from models import db, Investigation, InvestigationStatus, Evidence, Job
except ImportError:
    from manager.models import db, Investigation, InvestigationStatus, Evidence, Job

investigation_bp = Blueprint('investigations', __name__, url_prefix='/api/v1')


@investigation_bp.route('/investigations', methods=['POST'])
def create_investigation():
    """
    Create a new investigation.
    Expected JSON:
    {
      "name": "Network Investigation",
      "description": "Investigating network activity"
    }
    """
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON: expected JSON object"}), 400

    name = data.get("name")
    if not name or not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Missing required field 'name'"}), 400

    investigation = Investigation(
        name=name.strip(),
        description=data.get("description"),
        investigation_id=data.get("investigation_id"),
    )
    db.session.add(investigation)
    db.session.commit()

    return jsonify(investigation.to_dict()), 201


@investigation_bp.route('/investigations', methods=['GET'])
def list_investigations():
    """List all investigations."""
    investigations = Investigation.query.order_by(Investigation.created_at.desc()).all()
    return jsonify([i.to_dict() for i in investigations]), 200


@investigation_bp.route('/investigations/<investigation_id>', methods=['GET'])
def get_investigation(investigation_id):
    """Get details of a specific investigation."""
    investigation = db.session.get(Investigation, investigation_id)
    if not investigation:
        return jsonify({"error": "Investigation not found"}), 404
    return jsonify(investigation.to_dict()), 200


@investigation_bp.route('/investigations/<investigation_id>/results', methods=['GET'])
def get_investigation_results(investigation_id):
    """
    Get all results/evidence for an investigation.
    Aggregates across all jobs belonging to this investigation.
    """
    investigation = db.session.get(Investigation, investigation_id)
    if not investigation:
        return jsonify({"error": "Investigation not found"}), 404

    jobs = Job.query.filter_by(investigation_id=investigation_id).all()
    results = []
    for job in jobs:
        evidence = Evidence.query.filter_by(job_id=job.job_id).all()
        results.append({
            "job_id": job.job_id,
            "agent_id": job.agent_id,
            "status": job.status,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "evidence": [e.to_dict() for e in evidence],
        })

    return jsonify({
        "investigation_id": investigation_id,
        "name": investigation.name,
        "status": investigation.status,
        "jobs": results,
    }), 200
