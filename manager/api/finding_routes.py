from flask import Blueprint, jsonify, request
from models import db, Finding

finding_bp = Blueprint("finding", __name__, url_prefix="/api/v1/finding")


@finding_bp.get("/list")
def list_findings():
    query = Finding.query
    if request.args.get("agent_id"):
        query = query.filter_by(agent_id=request.args["agent_id"])
    if request.args.get("severity"):
        query = query.filter_by(severity=request.args["severity"])
    return jsonify([finding.to_dict() for finding in query.order_by(Finding.created_at.desc()).all()]), 200


@finding_bp.get("/<finding_id>")
def get_finding(finding_id):
    finding = Finding.query.get(finding_id)
    if not finding:
        return jsonify({"error": "Finding not found"}), 404
    return jsonify(finding.to_dict()), 200


@finding_bp.post("")
def create_finding():
    data = request.get_json()
    required = ("result_id", "agent_id", "category", "title", "description")
    if not isinstance(data, dict) or any(not data.get(field) for field in required):
        return jsonify({"error": "result_id, agent_id, category, title, and description required"}), 400
    finding = Finding(
        result_id=data["result_id"],
        agent_id=data["agent_id"],
        severity=data.get("severity", "medium"),
        category=data["category"],
        title=data["title"],
        description=data["description"],
        evidence=data.get("evidence"),
    )
    db.session.add(finding)
    db.session.commit()
    return jsonify(finding.to_dict()), 201


@finding_bp.patch("/<finding_id>")
def update_finding(finding_id):
    finding = Finding.query.get(finding_id)
    if not finding:
        return jsonify({"error": "Finding not found"}), 404
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON"}), 400
    for field in ("severity", "category", "title", "description", "status", "evidence"):
        if field in data:
            setattr(finding, field, data[field])
    db.session.commit()
    return jsonify(finding.to_dict()), 200
