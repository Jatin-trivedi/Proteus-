from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from models import db, Script, Deploy, Agent

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


# ==================== UPDATED DEPLOY ENDPOINT ====================
@script_bp.route('/deploy', methods=['POST'])
def deploy_script():
    """
    Create a script and deploy it to one or more agents in one call.
    Expected JSON:
    {
        "name": "MyScript",
        "agent_ids": ["agent-001", "agent-002"],
        "code": "agent my_script { ... }"
    }
    """
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON'}), 400

    name = data.get('name')
    agent_ids = data.get('agent_ids')
    code = data.get('code')

    if not name or not agent_ids or not code:
        return jsonify({'error': 'name, agent_ids, and code required'}), 400

    if not isinstance(agent_ids, list):
        return jsonify({'error': 'agent_ids must be a list'}), 400

    # 1. Create the script
    script = Script(
        script_id=str(uuid.uuid4()),
        name=name,
        code=code,
        created_at=datetime.utcnow()
    )
    db.session.add(script)
    db.session.commit()

    # 2. Deploy to each agent
    deploy_ids = []
    for agent_id in agent_ids:
        agent = Agent.query.get(agent_id)
        if not agent:
            # Optionally skip or return error; for now we skip non‑existent agents
            continue

        # Check if there's already a pending deployment for this agent/script
        existing = Deploy.query.filter_by(
            agent_id=agent_id,
            script_id=script.script_id,
            status='pending'
        ).first()
        if existing:
            # If already pending, reuse its ID? For now, skip.
            continue

        deploy = Deploy(
            deploy_id=str(uuid.uuid4()),
            agent_id=agent_id,
            script_id=script.script_id,
            status='pending'
        )
        db.session.add(deploy)
        deploy_ids.append(deploy.deploy_id)

    db.session.commit()

    return jsonify({
        'script_id': script.script_id,
        'deploy_ids': deploy_ids
    }), 201