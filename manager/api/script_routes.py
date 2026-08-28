from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from models import db, Script, Deploy, Agent   # added Agent import

script_bp = Blueprint('script', __name__, url_prefix='/api/v1/script')


@script_bp.route('/', methods=['POST'], strict_slashes=False)
def create_script():
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON'}), 400

    name = data.get('name')
    code = data.get('code')
    hash_before = data.get('hash_before')

    if not name or not code:
        return jsonify({'error': 'name and code required'}), 400

    script = Script(
        script_id=str(uuid.uuid4()),
        name=name,
        code=code,
        hash_before=hash_before,
        created_at=datetime.utcnow()
    )
    db.session.add(script)
    db.session.commit()

    return jsonify({
        'script_id': script.script_id,
        'name': script.name,
        'hash_before': script.hash_before
    }), 201


@script_bp.route('/<script_id>', methods=['GET'])
def get_script(script_id):
    script = Script.query.get(script_id)
    if not script:
        return jsonify({'error': 'Script not found'}), 404

    return jsonify({
        'script_id': script.script_id,
        'name': script.name,
        'code': script.code,
        'hash_before': script.hash_before,
        'hash_after': script.hash_after,
        'created_at': script.created_at.isoformat()
    })


@script_bp.route('/<script_id>/hash', methods=['POST'])
def update_script_hash(script_id):
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON'}), 400

    agent_id = data.get('agent_id')
    hash_after = data.get('hash_after')

    if not agent_id or not hash_after:
        return jsonify({'error': 'agent_id and hash_after required'}), 400

    script = Script.query.get(script_id)
    if not script:
        return jsonify({'error': 'Script not found'}), 404

    script.hash_after = hash_after
    db.session.commit()

    deploy = Deploy.query.filter_by(
        script_id=script_id,
        agent_id=agent_id
    ).first()
    if deploy:
        deploy.status = 'obfuscated'
        db.session.commit()

    return jsonify({'status': 'ok', 'hash_after': hash_after})


# ==================== NEW ENDPOINT ====================
@script_bp.route('/deploy', methods=['POST'])
def deploy_script():
    """
    Deploy a script to an agent.
    Expected JSON: { "agent_id": "...", "script_id": "..." }
    """
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON'}), 400

    agent_id = data.get('agent_id')
    script_id = data.get('script_id')

    if not agent_id or not script_id:
        return jsonify({'error': 'agent_id and script_id required'}), 400

    agent = Agent.query.get(agent_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404

    script = Script.query.get(script_id)
    if not script:
        return jsonify({'error': 'Script not found'}), 404

    existing = Deploy.query.filter_by(
        agent_id=agent_id,
        script_id=script_id,
        status='pending'
    ).first()
    if existing:
        return jsonify({'error': 'Deployment already pending'}), 400

    deploy = Deploy(
        deploy_id=str(uuid.uuid4()),
        agent_id=agent_id,
        script_id=script_id,
        status='pending'
    )
    db.session.add(deploy)
    db.session.commit()

    return jsonify({
        'deploy_id': deploy.deploy_id,
        'agent_id': deploy.agent_id,
        'script_id': deploy.script_id,
        'status': deploy.status,
        'deployed_at': deploy.deployed_at.isoformat()
    }), 201