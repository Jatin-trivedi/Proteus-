from flask import Blueprint, request, jsonify, send_file
from models import db, Result, Deploy
import io
import json

result_bp = Blueprint("result", __name__)

@result_bp.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    agent_id = data.get("agent_id")
    script_id = data.get("script_id")
    encrypted_data = data.get("data_enc")   # Already AES-GCM encrypted on agent

    if not all([agent_id, script_id, encrypted_data]):
        return jsonify({"error": "Missing fields"}), 400

    # Store result
    result = Result(
        agent_id=agent_id,
        script_id=script_id,
        data_encrypted=encrypted_data
    )
    db.session.add(result)
    db.session.commit()

    # Find associated deploy and mark as executed
    deploy = Deploy.query.filter_by(agent_id=agent_id, script_id=script_id, status="delivered").first()
    if deploy:
        deploy.status = "executed"
        deploy.result_id = result.result_id
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

    # For demo, we return the encrypted data – in real world, you'd decrypt server‑side
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

    # In a real scenario, decrypt and format
    data = {
        "result_id": result.result_id,
        "agent": result.agent_id,
        "script": result.script_id,
        "data": result.data_encrypted  # placeholder
    }
    if fmt == "json":
        return jsonify(data), 200
    else:
        # CSV or other – for demo, just return JSON as file
        json_str = json.dumps(data, indent=2)
        return send_file(
            io.BytesIO(json_str.encode()),
            mimetype="application/json",
            as_attachment=True,
            download_name=f"result_{result_id}.json"
        )