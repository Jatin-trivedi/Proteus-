from flask import Blueprint, request, jsonify
from models import db, Agent
from datetime import datetime

agent_bp = Blueprint("agent", __name__)

@agent_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    required = ["agent_id", "os", "ip", "arch"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    agent = Agent.query.get(data["agent_id"])
    if agent:
        # Re‑register – update token and info
        agent.os = data["os"]
        agent.ip = data["ip"]
        agent.arch = data["arch"]
        agent.token = Agent._generate_token()
        agent.status = "online"
        agent.last_seen = datetime.utcnow()
    else:
        agent = Agent(data["agent_id"], data["os"], data["ip"], data["arch"])
        db.session.add(agent)

    db.session.commit()
    return jsonify({"token": agent.token, "status": "registered"}), 200

@agent_bp.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.get_json()
    agent_id = data.get("agent_id")
    token = data.get("token")
    if not agent_id or not token:
        return jsonify({"error": "Missing agent_id or token"}), 400

    agent = Agent.query.get(agent_id)
    if not agent or agent.token != token:
        return jsonify({"error": "Invalid token"}), 401

    agent.update_heartbeat()
    db.session.commit()

    # Check if any pending deploy exists for this agent
    from models import Deploy
    pending = Deploy.query.filter_by(agent_id=agent_id, status="pending").first()
    next_task_id = pending.deploy_id if pending else None

    return jsonify({"next_task_id": next_task_id}), 200

@agent_bp.route("/status", methods=["GET"])
def status():
    agent_id = request.args.get("agent_id")
    if not agent_id:
        return jsonify({"error": "agent_id required"}), 400
    agent = Agent.query.get(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    return jsonify({
        "status": agent.status,
        "last_seen": agent.last_seen.isoformat()
    }), 200