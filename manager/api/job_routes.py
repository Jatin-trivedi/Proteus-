"""
Proteus Manager — Job API Routes (Priority 7)

Endpoints for job lifecycle: creation, polling, acknowledgement,
result upload, cancellation, and retrieval.
"""

from flask import Blueprint, request, jsonify

try:
    from job_service import JobService, IRValidationError
    from middleware.agent_auth import agent_token_required
    from models import db, Agent
except ImportError:
    from manager.job_service import JobService, IRValidationError
    from manager.middleware.agent_auth import agent_token_required
    from manager.models import db, Agent

job_bp = Blueprint('jobs', __name__, url_prefix='/api/v1')


@job_bp.route('/jobs', methods=['POST'])
def create_job():
    """
    Create a new forensic job.
    Expected JSON:
    {
      "agent_id": "...",
      "investigation_id": "...",
      "ir": { "version": "1.0", "investigation": "...", "operations": [...] }
    }
    """
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON: expected JSON object"}), 400

    agent_id = data.get("agent_id")
    if not agent_id:
        return jsonify({"error": "Missing required field 'agent_id'"}), 400

    investigation_id = data.get("investigation_id")
    if not investigation_id:
        return jsonify({"error": "Missing required field 'investigation_id'"}), 400

    ir = data.get("ir")
    if not ir:
        return jsonify({"error": "Missing required field 'ir'"}), 400

    resp, status_code = JobService.create_job(agent_id, investigation_id, ir)
    return jsonify(resp), status_code


@job_bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List all jobs with optional filters: agent_id, investigation_id, status."""
    agent_id = request.args.get("agent_id")
    investigation_id = request.args.get("investigation_id")
    status = request.args.get("status")
    jobs = JobService.list_jobs(agent_id=agent_id, investigation_id=investigation_id, status=status)
    return jsonify(jobs), 200


@job_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get details of a specific job including evidence."""
    job = JobService.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job), 200


@job_bp.route('/agents/<agent_id>/jobs/next', methods=['GET'])
@agent_token_required
def poll_next_job(agent_id):
    """
    Agent polls for the next available job.
    Atomically claims the next ASSIGNED job for this agent.
    """
    if request.agent_id != agent_id:
        return jsonify({"error": "Unauthorized: cannot poll jobs for another agent"}), 403
    resp, status_code = JobService.claim_next_job(agent_id)
    return jsonify(resp), status_code


@job_bp.route('/jobs/<job_id>/ack', methods=['POST'])
@agent_token_required
def acknowledge_job(job_id):
    """
    Agent acknowledges receipt of a job.
    Transitions ASSIGNED → RUNNING.
    Requires agent_id in request body.
    """
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON: expected JSON object"}), 400

    agent_id = data.get("agent_id")
    if not agent_id:
        return jsonify({"error": "Missing required field 'agent_id'"}), 400

    if request.agent_id != agent_id:
        return jsonify({"error": "Unauthorized: cannot acknowledge jobs for another agent"}), 403

    resp, status_code = JobService.acknowledge_job(job_id, agent_id)
    return jsonify(resp), status_code


@job_bp.route('/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel a job (QUEUED or ASSIGNED → CANCELLED)."""
    resp, status_code = JobService.cancel_job(job_id)
    return jsonify(resp), status_code


@job_bp.route('/jobs/<job_id>/results', methods=['POST'])
@agent_token_required
def submit_results(job_id):
    """
    Agent uploads forensic execution results.
    Validates agent ownership, job state, and evidence integrity.
    Expected JSON:
    {
      "agent_id": "...",
      "status": "completed|failed",
      "results": [...],
      "evidence": [...],
      "integrity": { "algorithm": "SHA-256", "hash": "..." },
      "error": "..." (optional, for failed jobs)
    }
    """
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON: expected JSON object"}), 400

    agent_id = data.get("agent_id")
    if not agent_id:
        return jsonify({"error": "Missing required field 'agent_id'"}), 400

    if request.agent_id != agent_id:
        return jsonify({"error": "Unauthorized: cannot submit results for another agent"}), 403

    resp, status_code = JobService.complete_job(job_id, agent_id, data)
    return jsonify(resp), status_code
