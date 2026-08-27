from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Agent, Deploy, Script

agent_bp = Blueprint('agent', __name__, url_prefix='/api/v1/agent')

@agent_bp.route('/register', methods=['POST'])
def register_agent():
    data = request.get_json()
    agent_id = data.get('agent_id')
    hostname = data.get('hostname')
    os_type = data.get('os')

    if not agent_id:
        return jsonify({'error': 'agent_id required'}), 400

    agent = Agent.query.get(agent_id)
    if not agent:
        agent = Agent(
            agent_id=agent_id,   # adjust if your Agent model uses 'agent_id'
            hostname=hostname,
            os=os_type,
            status='offline',
            last_seen=None
        )
        db.session.add(agent)
    else:
        agent.hostname = hostname or agent.hostname
        agent.os = os_type or agent.os

    db.session.commit()
    return jsonify({'status': 'registered', 'agent_id': agent_id})


@agent_bp.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json()
    agent_id = data.get('agent_id')

    if not agent_id:
        return jsonify({'error': 'agent_id required'}), 400

    agent = Agent.query.get(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404

    agent.last_seen = datetime.utcnow()
    agent.status = 'online'
    db.session.commit()

    # Check for pending deployments for this agent
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
            # Mark as in_progress
            pending.status = 'in_progress'
            db.session.commit()

    return jsonify(response)