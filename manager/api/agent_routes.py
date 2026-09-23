from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from sqlalchemy.exc import SQLAlchemyError
from models import db, Agent, Deploy, Script, Finding, Result
from middleware.auth import jwt_required
from agent_registry import AgentRegistry
from audit_logger import log_event, AuditEvent

agent_bp = Blueprint('agent', __name__, url_prefix='/api/v1/agent')


@agent_bp.route('/register', methods=['POST'])
def register_agent():
    """
    Register a new agent or update an existing one.
    Accepts formal AgentRegistrationRequest or legacy payload.
    Expected JSON:
    {
      "hostname": "...",
      "os": "windows|linux",
      "architecture": "...",
      "version": "...",
      "capabilities": [...]
    }
    """
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON: expected JSON object'}), 400

    resp_data, status_code = AgentRegistry.register_agent(data)
    return jsonify(resp_data), status_code


@agent_bp.route('/', methods=['GET'], strict_slashes=False)
@agent_bp.route('/list', methods=['GET'])
def list_agents():
    """List all registered agents."""
    status_filter = request.args.get("status")
    agents = AgentRegistry.list_agents(status_filter=status_filter)
    return jsonify(agents), 200


@agent_bp.route('/<agent_id>', methods=['GET'])
@agent_bp.route('/status/<agent_id>', methods=['GET'])
def get_agent_status(agent_id):
    """Get details/status of a specific agent."""
    agent_dict = AgentRegistry.get_agent(agent_id)
    if not agent_dict:
        return jsonify({'error': 'Agent not found'}), 404
    return jsonify(agent_dict), 200


@agent_bp.route('/heartbeat', methods=['POST'])
def heartbeat():
    """
    Agent heartbeat – validates agent identity, updates last_heartbeat/status,
    records current_job, and returns heartbeat response.
    Expected JSON: { "agent_id": "...", "status": "online|busy|error|offline", "current_job": "..." }
    """
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON: expected JSON object'}), 400

    resp_data, status_code = AgentRegistry.update_heartbeat(data)
    if status_code != 200:
        return jsonify(resp_data), status_code

    log_event(
        AuditEvent.AGENT_HEARTBEAT,
        agent_id=data.get("agent_id"),
        detail="Agent heartbeat received",
        extra={"status": data.get("status"), "current_job": data.get("current_job")},
    )

    agent_id = data.get('agent_id')
    # Backward compatibility: attach pending deploy if one exists
    try:
        pending = Deploy.query.filter_by(
            agent_id=agent_id,
            status='pending'
        ).first()

        if pending:
            script = Script.query.get(pending.script_id)
            if script:
                agent = db.session.get(Agent, agent_id)
                if agent and script.code == '__exit__':
                    agent.status = 'decommissioning'
                resp_data['deployment'] = {
                    'deploy_id': pending.deploy_id,
                    'script_id': script.script_id,
                    'code': script.code,
                    'hash_before': script.hash_before
                }
                pending.status = 'in_progress'
                db.session.commit()
    except Exception:
        pass

    return jsonify(resp_data), 200


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
