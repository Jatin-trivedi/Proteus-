from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
from models import db, Result, Deploy
import uuid
import io
import json

result_bp = Blueprint("result", __name__, url_prefix='/api/v1/result')


@result_bp.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON'}), 400

    agent_id = data.get("agent_id")
    script_id = data.get("script_id")
    encrypted_data = data.get("data_enc")

    if not all([agent_id, script_id, encrypted_data]):
        return jsonify({"error": "Missing fields"}), 400

    result = Result(
        result_id=str(uuid.uuid4()),
        agent_id=agent_id,
        script_id=script_id,
        data_encrypted=encrypted_data,
        submitted_at=datetime.utcnow()
    )
    db.session.add(result)
    db.session.commit()

    deploy = Deploy.query.filter_by(
        agent_id=agent_id,
        script_id=script_id
    ).order_by(Deploy.executed_at.desc()).first()
    if deploy:
        deploy.status = "completed"
        deploy.result_id = result.result_id
        deploy.executed_at = datetime.utcnow()
        db.session.commit()

    return jsonify({"result_id": result.result_id}), 200


@result_bp.route("/view", methods=["GET"])
def view():
    result_id = request.args.get("result_id")
    if not result_id:
        return jsonify({"error": "result_id required"}), 400

    result = Result.query.get(result_id)
    if not result:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "result_id": result.result_id,
        "agent_id": result.agent_id,
        "script_id": result.script_id,
        "data_encrypted": result.data_encrypted,
        "submitted_at": result.submitted_at.isoformat()
    }), 200


@result_bp.route("/export", methods=["GET"])
def export():
    result_id = request.args.get("result_id")
    fmt = request.args.get("fmt", "json")

    if not result_id:
        return jsonify({"error": "result_id required"}), 400

    result = Result.query.get(result_id)
    if not result:
        return jsonify({"error": "Not found"}), 404

    data = {
        "result_id": result.result_id,
        "agent_id": result.agent_id,
        "script_id": result.script_id,
        "encrypted_data": result.data_encrypted,
        "submitted_at": result.submitted_at.isoformat()
    }

    if fmt == "json":
        return jsonify(data), 200
    else:
        json_str = json.dumps(data, indent=2)
        return send_file(
            io.BytesIO(json_str.encode()),
            mimetype="application/json",
            as_attachment=True,
            download_name=f"result_{result_id}.json"
        )


# ==================== NEW ENDPOINT ====================
@result_bp.route("/list", methods=["GET"])
def list_results():
    """
    List all results (optionally filter by agent_id).
    Query param: ?agent_id=...
    """
    agent_id = request.args.get("agent_id")
    query = Result.query
    if agent_id:
        query = query.filter_by(agent_id=agent_id)
    results = query.order_by(Result.submitted_at.desc()).all()

    return jsonify([{
        "result_id": r.result_id,
        "agent_id": r.agent_id,
        "script_id": r.script_id,
        "submitted_at": r.submitted_at.isoformat(),
        "data_encrypted": r.data_encrypted[:50] + "..." if r.data_encrypted and len(r.data_encrypted) > 50 else r.data_encrypted
    } for r in results]), 200