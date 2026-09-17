from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from sqlalchemy.exc import SQLAlchemyError
from models import db, Agent, Deploy, Script, Finding, Result
from middleware.auth import jwt_required

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

    agent = Agent.query.get(agent_id)
    if not agent:
        agent = Agent(
            agent_id=agent_id,
            hostname=hostname,
            os=os_type,
            ip=ip,
            arch=arch
        )
        db.session.add(agent)
    else:
        agent.hostname = hostname or agent.hostname
        agent.os = os_type or agent.os
        agent.ip = ip or agent.ip
        agent.arch = arch or agent.arch

    db.session.commit()
    return jsonify({'status': 'registered', 'agent_id': agent_id}), 200


@agent_bp.route('/heartbeat', methods=['POST'])
def heartbeat():
    """
    Agent heartbeat ? updates last_seen and returns pending deployments.
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

    agent.last_seen = datetime.utcnow()
    agent.status = 'online'
    db.session.commit()

    pending = Deploy.query.filter_by(
        agent_id=agent_id,
        status='pending'
    ).first()

    response = {'status': 'ok'}

    if pending:
        script = Script.query.get(pending.script_id)
        if script:
            if script.code == '__exit__':
                agent.status = 'decommissioning'
            response['deployment'] = {
                'deploy_id': pending.deploy_id,
                'script_id': script.script_id,
                'code': script.code,
                'hash_before': script.hash_before
            }
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


# ==================== NEW ENDPOINT ====================
@agent_bp.route('/list', methods=['GET'])
def list_agents():
    """List all registered agents."""
    agents = Agent.query.all()
    return jsonify([{
        'agent_id': a.agent_id,
        'hostname': a.hostname,
        'os': a.os,
        'ip': a.ip,
        'arch': a.arch,
        'status': a.status,
        'last_seen': a.last_seen.isoformat() if a.last_seen else None
    } for a in agents]), 200


@agent_bp.route('/<agent_id>/decommission', methods=['POST'])
@jwt_required
def decommission_agent(agent_id):
    """Queue the kill switch for an agent without deleting its audit record."""
    agent = Agent.query.get(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404

    existing = (
        Deploy.query
        .join(Script)
        .filter(
            Deploy.agent_id == agent_id,
            Deploy.status == 'pending',
            Script.name == 'kill-switch',
            Script.code == '__exit__'
        )
        .first()
    )
    if existing:
        agent.status = 'decommissioning'
        db.session.commit()
        return jsonify({
            'status': 'already_queued',
            'agent_id': agent_id,
            'script_id': existing.script_id,
            'deploy_id': existing.deploy_id
        }), 200

    script = Script(
        script_id=str(uuid.uuid4()),
        name='kill-switch',
        code='__exit__',
        created_at=datetime.utcnow()
    )
    deployment = Deploy(
        deploy_id=str(uuid.uuid4()),
        agent_id=agent_id,
        script_id=script.script_id,
        status='pending'
    )
    agent.status = 'decommissioning'

    try:
        db.session.add(script)
        db.session.add(deployment)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({'error': 'Failed to queue agent decommission'}), 500

    return jsonify({
        'status': 'queued',
        'agent_id': agent_id,
        'script_id': script.script_id,
        'deploy_id': deployment.deploy_id
    }), 202


@agent_bp.route('/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """Delete an agent and all related deployments, results, and findings."""
    agent = Agent.query.get(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404

    try:
        results = Result.query.filter_by(agent_id=agent_id).all()
        result_ids = [result.result_id for result in results]

        # Remove dependents that may reference the agent's results.
        if result_ids:
            Finding.query.filter(
                (Finding.agent_id == agent_id) | (Finding.result_id.in_(result_ids))
            ).delete(synchronize_session=False)
            Deploy.query.filter(
                (Deploy.agent_id == agent_id) | (Deploy.result_id.in_(result_ids))
            ).delete(synchronize_session=False)
        else:
            Finding.query.filter_by(agent_id=agent_id).delete(synchronize_session=False)
            Deploy.query.filter_by(agent_id=agent_id).delete(synchronize_session=False)

        Result.query.filter_by(agent_id=agent_id).delete(synchronize_session=False)
        db.session.delete(agent)
        db.session.commit()
        return jsonify({'status': 'deleted', 'agent_id': agent_id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete agent: {str(e)}'}), 500
