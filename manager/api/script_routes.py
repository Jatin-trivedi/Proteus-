from flask import Blueprint, request, jsonify
from models import db, Script, Deploy, Agent
import hashlib
import uuid

script_bp = Blueprint("script", __name__)

@script_bp.route("/deploy", methods=["POST"])
def deploy():
    data = request.get_json()
    code = data.get("code")
    agent_ids = data.get("agent_ids", [])
    name = data.get("name", "Untitled")

    if not code:
        return jsonify({"error": "Missing code"}), 400

    # Compute hash of the raw code (for integrity check on agent)
    code_hash = hashlib.sha256(code.encode()).hexdigest()

    # Store script
    script = Script(name=name, code=code, hash=code_hash)
    db.session.add(script)
    db.session.commit()

    # Create deploy records for each agent
    deploy_ids = []
    for aid in agent_ids:
        agent = Agent.query.get(aid)
        if not agent:
            continue
        deploy = Deploy(script_id=script.script_id, agent_id=aid, status="pending")
        db.session.add(deploy)
        db.session.commit()
        deploy_ids.append(deploy.deploy_id)

    return jsonify({"deploy_ids": deploy_ids, "script_id": script.script_id}), 200

@script_bp.route("/list", methods=["GET"])
def list_scripts():
    scripts = Script.query.all()
    return jsonify([{
        "script_id": s.script_id,
        "name": s.name,
        "hash": s.hash,
        "created_at": s.created_at.isoformat()
    } for s in scripts]), 200

@script_bp.route("/fetch", methods=["GET"])
def fetch_script():
    deploy_id = request.args.get("deploy_id")
    agent_id = request.args.get("agent_id")
    if not deploy_id or not agent_id:
        return jsonify({"error": "deploy_id and agent_id required"}), 400

    deploy = Deploy.query.filter_by(deploy_id=deploy_id, agent_id=agent_id).first()
    if not deploy:
        return jsonify({"error": "Deploy not found"}), 404

    script = Script.query.get(deploy.script_id)
    if not script:
        return jsonify({"error": "Script not found"}), 404

    # Update status to delivered
    deploy.status = "delivered"
    db.session.commit()

    return jsonify({
        "jocky_code": script.code,
        "hash": script.hash,
        "script_id": script.script_id
    }), 200