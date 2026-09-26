from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import os
import sys
import uuid

from models import db, Script, Deploy, Agent, Result, Finding
from middleware.auth import jwt_required

script_bp = Blueprint('script', __name__, url_prefix='/api/v1/script')


# ─────────────────────────────────────────────────────────────────────────────
# Compiler helper
# ─────────────────────────────────────────────────────────────────────────────

def _compile_jocky_to_ir(source: str) -> tuple[str | None, str | None]:
    """
    Compile a JOCKY source string into an IRDocument JSON string.

    Returns:
        (ir_json, None)          on success
        (None,    error_message) on failure

    The manager sits at  repo/manager/api/script_routes.py
    The compiler sits at repo/compiler/
    We add the repo root to sys.path so `from compiler.compiler import Compiler`
    works both locally and on Vercel (where PYTHONPATH includes repo root).
    """
    try:
        repo_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..')
        )
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)

        from compiler.compiler import Compiler  # noqa: PLC0415

        result = Compiler().compile(source, filename='<deploy>')

        if not result.success:
            # Format the first few diagnostics as a readable error string
            msgs = [
                f"[{d.severity}] line {d.line}: {d.message}"
                for d in result.diagnostics[:5]
            ]
            return None, '\n'.join(msgs) or 'Compilation failed (unknown error)'

        if not result.ir:
            return None, 'Compiler returned no IR output'

        return json.dumps(result.ir), None

    except ImportError as exc:
        # Compiler package not on path — degrade gracefully
        return None, f'Compiler not available: {exc}'
    except Exception as exc:  # noqa: BLE001
        return None, f'Unexpected compiler error: {exc}'


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

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
        created_at=datetime.utcnow(),
    )
    db.session.add(script)
    db.session.commit()

    return jsonify({
        'script_id': script.script_id,
        'name': script.name,
        'hash_before': script.hash_before,
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
        'created_at': script.created_at.isoformat(),
    })


@script_bp.route('/list', methods=['GET'])
def list_scripts():
    """List scripts available to the React dashboard."""
    scripts = Script.query.order_by(Script.created_at.desc()).all()
    return jsonify([script.to_dict() for script in scripts]), 200


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
        agent_id=agent_id,
    ).first()
    if deploy:
        deploy.status = 'obfuscated'
        db.session.commit()

    return jsonify({'status': 'ok', 'hash_after': hash_after})


@script_bp.route('/deploy', methods=['POST'])
def deploy_script():
    """
    Compile a JOCKY script and deploy it to one or more agents.

    Request JSON:
    {
        "name":      "MyScript",
        "agent_ids": ["agent-001", "agent-002"],
        "code":      "agent my_script { ... }"   ← raw JOCKY source
    }

    Pipeline:
        1. Validate input
        2. Compile JOCKY source → IRDocument JSON   ← NEW
        3. Persist Script (storing IR JSON as code)  ← CHANGED
        4. Create Deploy rows for each target agent
    """
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON'}), 400

    name      = data.get('name')
    agent_ids = data.get('agent_ids')
    raw_code  = data.get('code')

    if not name or not agent_ids or not raw_code:
        return jsonify({'error': 'name, agent_ids, and code required'}), 400
    if not isinstance(agent_ids, list):
        return jsonify({'error': 'agent_ids must be a list'}), 400

    # ── Compile JOCKY → IR JSON ───────────────────────────────────────────
    # Special built-in commands (kill-switch etc.) bypass compilation.
    BUILTINS = {'__exit__', 'exit', 'kill', '__kill__'}

    compilation_warning = None

    if raw_code.strip().lower() in BUILTINS:
        # Pass built-in commands through unchanged
        payload_code = raw_code
    else:
        ir_json, compile_error = _compile_jocky_to_ir(raw_code)

        if ir_json:
            # Success: agent will receive IRDocument JSON and execute it
            # through executeIRDocumentJSON → typed dispatch
            payload_code = ir_json
        else:
            # Compilation failed. Two options:
            #   a) Reject the deployment (strict mode)
            #   b) Store raw JOCKY so the agent's legacy fallback handles it
            #
            # We choose (b) so the manager never silently blocks a deploy —
            # the agent logs a warning if it can't parse the payload as IR.
            payload_code = raw_code
            compilation_warning = compile_error
            print(f'[WARN] JOCKY compilation failed for "{name}": {compile_error}')

    # ── Persist Script ────────────────────────────────────────────────────
    script = Script(
        script_id=str(uuid.uuid4()),
        name=name,
        # code holds the IR JSON (or raw JOCKY as fallback)
        code=payload_code,
        # Preserve original source so analysts can review/edit it later
        hash_before=data.get('hash_before'),
        created_at=datetime.utcnow(),
    )
    db.session.add(script)
    db.session.commit()

    # ── Create Deploy rows ────────────────────────────────────────────────
    deploy_ids = []
    skipped_agents = []

    for agent_id in agent_ids:
        agent = Agent.query.get(agent_id)
        if not agent:
            skipped_agents.append(agent_id)
            continue

        existing = Deploy.query.filter_by(
            agent_id=agent_id,
            script_id=script.script_id,
            status='pending',
        ).first()
        if existing:
            continue

        deploy = Deploy(
            deploy_id=str(uuid.uuid4()),
            agent_id=agent_id,
            script_id=script.script_id,
            status='pending',
        )
        db.session.add(deploy)
        deploy_ids.append(deploy.deploy_id)

    db.session.commit()

    # ── Response ──────────────────────────────────────────────────────────
    response = {
        'script_id':  script.script_id,
        'deploy_ids': deploy_ids,
        'compiled':   compilation_warning is None and raw_code.strip().lower() not in BUILTINS,
    }
    if skipped_agents:
        response['skipped_agents'] = skipped_agents
    if compilation_warning:
        response['warning'] = compilation_warning

    return jsonify(response), 201


@script_bp.route('/deployments', methods=['GET'])
def list_deployments():
    """List deployments with context for the operations dashboard."""
    deployments = Deploy.query.order_by(Deploy.deployed_at.desc()).all()
    return jsonify([{
        **deployment.to_dict(),
        'script_name': deployment.script.name if deployment.script else None,
        'hostname':    deployment.agent.hostname if deployment.agent else None,
    } for deployment in deployments]), 200


@script_bp.route('/<script_id>', methods=['DELETE'])
@jwt_required
def delete_script(script_id):
    script = Script.query.get(script_id)
    if not script:
        return jsonify({'error': 'Script not found'}), 404

    result_ids = [
        result.result_id
        for result in Result.query.filter_by(script_id=script_id).all()
    ]
    if result_ids:
        Finding.query.filter(
            Finding.result_id.in_(result_ids)
        ).delete(synchronize_session=False)
        Deploy.query.filter(
            Deploy.result_id.in_(result_ids)
        ).update({'result_id': None}, synchronize_session=False)
        Result.query.filter(
            Result.result_id.in_(result_ids)
        ).delete(synchronize_session=False)

    Deploy.query.filter_by(script_id=script_id).delete(synchronize_session=False)
    db.session.delete(script)
    db.session.commit()
    return jsonify({'status': 'deleted', 'script_id': script_id}), 200