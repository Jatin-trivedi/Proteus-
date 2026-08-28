from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Agent, Deploy, Script

agent_bp = Blueprint('agent', __name__, url_prefix='/api/v1/agent')


@agent_bp.route('/register', methods=['POST'])
def register_agent():
    """
    Register a new agent or update an existing one.
    Expected JSON: { "agent_id": "...", "hostname": "...", "os": "...", "ip": "...", "arch": "..." }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    agent_id = data.get('agent_id')
    hostname = data.get('hostname', 'unknown')
    os_type = data.get('os', 'unknown')
    ip = data.get('ip', '0.0.0.0')
    arch = data.get('arch', 'unknown')

    if not agent_id:
        return jsonify({'error': 'agent_id required'}), 400

    # Check if agent already exists
    agent = Agent.query.get(agent_id)
    if not agent:
        # Create new agent
        agent = Agent(
            agent_id=agent_id,
            hostname=hostname,
            os=os_type,
            ip=ip,
            arch=arch
        )
        db.session.add(agent)
    else:
        # Update existing agent's info (if provided)
        agent.hostname = hostname or agent.hostname
        agent.os = os_type or agent.os
        agent.ip = ip or agent.ip
        agent.arch = arch or agent.arch

    db.session.commit()
    return jsonify({'status': 'registered', 'agent_id': agent_id}), 200


@agent_bp.route('/heartbeat', methods=['POST'])
def heartbeat():
    """
    Agent heartbeat – updates last_seen and returns pending deployments.
    Expected JSON: { "agent_id": "..." }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    agent_id = data.get('agent_id')
    if not agent_id:
        return jsonify({'error': 'agent_id required'}), 400

    agent = Agent.query.get(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404

    # Update heartbeat timestamp and status
    agent.last_seen = datetime.utcnow()
    agent.status = 'online'
    db.session.commit()

    # Check for any pending deployments for this agent
    pending = Deploy.query.filter_by(
        agent_id=agent_id,
        status='pending'
    ).first()

    response = {'status': 'ok'}

    if pending:
        script = Script.query.get(pending.script_id)
        if script:
            response['deployment'] = {
                'deploy_id': pending.deploy_id,
                'script_id': script.script_id,
                'code': script.code,
                'hash_before': script.hash_before
            }
            # Mark as in_progress so it's not returned again
            pending.status = 'in_progress'
            db.session.commit()

    return jsonify(response), 200


@agent_bp.route('/status/<agent_id>', methods=['GET'])
def get_agent_status(agent_id):
    """Get status of a specific agent."""
    agent = Agent.query.get(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404

    return jsonify({
        'agent_id': agent.agent_id,
        'hostname': agent.hostname,
        'os': agent.os,
        'ip': agent.ip,
        'arch': agent.arch,
        'status': agent.status,
        'last_seen': agent.last_seen.isoformat() if agent.last_seen else None
    }), 200