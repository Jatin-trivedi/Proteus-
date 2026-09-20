"""
Proteus Manager — Job Service (Priority 7)

Encapsulates job lifecycle management, IR validation, atomic job claiming,
and result processing. Acts as the service/repository layer between API routes
and the database.
"""

from datetime import datetime, timezone
import hashlib
import json
import threading
from typing import Any, Dict, List, Optional, Tuple

try:
    from models import db, Job, JobStatus, JobTransitionError, Agent, Investigation, Evidence
    from audit_logger import log_event, AuditEvent
except ImportError:
    from manager.models import db, Job, JobStatus, JobTransitionError, Agent, Investigation, Evidence
    from manager.audit_logger import log_event, AuditEvent

try:
    from runtime.registry import APPROVED_OPERATIONS
except ImportError:
    APPROVED_OPERATIONS = {
        "system.info", "system.users",
        "processes.list", "processes.details",
        "network.interfaces", "network.connections",
        "network.routes", "network.dns",
        "filesystem.metadata", "filesystem.hash",
    }


# Application-level lock for atomic job claiming (SQLite doesn't support SELECT FOR UPDATE)
_claim_lock = threading.Lock()

SUPPORTED_IR_VERSIONS = {"1.0"}


class IRValidationError(ValueError):
    """Raised when IR validation fails on the server side."""
    pass


class JobService:
    """Service layer for job lifecycle management."""

    @staticmethod
    def validate_ir(ir_dict: Dict[str, Any]) -> None:
        """
        Server-side IR validation. Rejects malformed or unauthorized IR.
        Raises IRValidationError on failure.
        """
        if not isinstance(ir_dict, dict):
            raise IRValidationError("IR must be a JSON object")

        # Version check
        version = ir_dict.get("version")
        if not version or not isinstance(version, str):
            raise IRValidationError("IR missing required field 'version'")
        if version not in SUPPORTED_IR_VERSIONS:
            raise IRValidationError(f"Unsupported IR version '{version}'. Supported: {sorted(SUPPORTED_IR_VERSIONS)}")

        # Investigation name
        investigation = ir_dict.get("investigation")
        if not investigation or not isinstance(investigation, str) or not investigation.strip():
            raise IRValidationError("IR missing required field 'investigation'")

        # Operations list
        operations = ir_dict.get("operations")
        if operations is None:
            raise IRValidationError("IR missing required field 'operations'")
        if not isinstance(operations, list):
            raise IRValidationError("IR 'operations' must be a list")
        if len(operations) == 0:
            raise IRValidationError("IR 'operations' must contain at least one operation")

        seen_ids = set()
        for i, op in enumerate(operations):
            if not isinstance(op, dict):
                raise IRValidationError(f"Operation at index {i} must be a JSON object")

            # Operation ID
            op_id = op.get("id")
            if not op_id or not isinstance(op_id, str) or not op_id.strip():
                raise IRValidationError(f"Operation at index {i} missing required field 'id'")
            if op_id in seen_ids:
                raise IRValidationError(f"Duplicate operation ID: '{op_id}'")
            seen_ids.add(op_id)

            # Operation type
            op_type = op.get("type")
            if not op_type or not isinstance(op_type, str) or not op_type.strip():
                raise IRValidationError(f"Operation '{op_id}' missing required field 'type'")
            if op_type not in APPROVED_OPERATIONS:
                raise IRValidationError(
                    f"Operation '{op_id}' has unapproved type '{op_type}'. "
                    f"Approved: {sorted(APPROVED_OPERATIONS)}"
                )

            # Parameters
            params = op.get("parameters")
            if params is not None and not isinstance(params, dict):
                raise IRValidationError(f"Operation '{op_id}' parameters must be a JSON object")

            # Reject suspicious executable fields
            for dangerous_key in ("code", "script", "shell", "command", "exec", "eval", "payload"):
                if dangerous_key in op:
                    raise IRValidationError(
                        f"Operation '{op_id}' contains forbidden field '{dangerous_key}'"
                    )

    @classmethod
    def create_job(
        cls,
        agent_id: str,
        investigation_id: str,
        ir_dict: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], int]:
        """
        Creates a new job after validating the IR and verifying the agent exists.
        Returns (response_dict, status_code).
        """
        # Validate agent exists
        agent = db.session.get(Agent, agent_id)
        if not agent:
            return {"error": f"Agent '{agent_id}' not found"}, 404

        # Validate IR
        try:
            cls.validate_ir(ir_dict)
        except IRValidationError as e:
            return {"error": f"Invalid IR: {str(e)}"}, 400

        # Create job
        job = Job(
            agent_id=agent_id,
            investigation_id=investigation_id,
            ir=ir_dict,
            status=JobStatus.QUEUED,
        )

        # Transition to ASSIGNED immediately (agent is known)
        job.transition_to(JobStatus.ASSIGNED)

        db.session.add(job)
        db.session.commit()

        log_event(
            AuditEvent.JOB_CREATED,
            agent_id=agent_id,
            job_id=job.job_id,
            investigation_id=investigation_id,
            detail="Job created and assigned",
        )
        return job.to_dict(), 201

    @classmethod
    def claim_next_job(cls, agent_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Atomically claims the next ASSIGNED job for the given agent.
        Uses application-level locking for SQLite compatibility.
        Returns (response_dict, status_code).
        """
        # Verify agent exists
        agent = db.session.get(Agent, agent_id)
        if not agent:
            return {"error": f"Agent '{agent_id}' not found"}, 404

        with _claim_lock:
            job = (
                Job.query
                .filter_by(agent_id=agent_id, status=JobStatus.ASSIGNED)
                .order_by(Job.created_at.asc())
                .first()
            )

            if not job:
                return {"job": None}, 200

            return {
                "job": {
                    "job_id": job.job_id,
                    "investigation_id": job.investigation_id,
                    "ir": job.get_ir_dict(),
                }
            }, 200

    @classmethod
    def acknowledge_job(cls, job_id: str, agent_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Agent acknowledges a job — transitions ASSIGNED → RUNNING.
        Verifies the requesting agent is the assigned agent.
        """
        job = db.session.get(Job, job_id)
        if not job:
            return {"error": f"Job '{job_id}' not found"}, 404

        if job.agent_id != agent_id:
            return {"error": "Unauthorized: agent is not assigned to this job"}, 403

        try:
            job.transition_to(JobStatus.RUNNING)
        except JobTransitionError as e:
            return {"error": str(e)}, 409

        # Update agent status to BUSY
        agent = db.session.get(Agent, agent_id)
        if agent:
            agent.status = "BUSY"
            agent.current_job = job_id

        db.session.commit()

        log_event(
            AuditEvent.JOB_STARTED,
            agent_id=agent_id,
            job_id=job_id,
            detail="Job acknowledged → RUNNING",
        )
        return {"status": "acknowledged", "job_id": job_id}, 200

    @classmethod
    def complete_job(
        cls,
        job_id: str,
        agent_id: str,
        result_data: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], int]:
        """
        Marks a job as COMPLETED and stores evidence.
        Verifies agent ownership, job is RUNNING, and evidence integrity.
        """
        job = db.session.get(Job, job_id)
        if not job:
            return {"error": f"Job '{job_id}' not found"}, 404

        if job.agent_id != agent_id:
            return {"error": "Unauthorized: agent is not assigned to this job"}, 403

        if job.status != JobStatus.RUNNING:
            return {"error": f"Job is not RUNNING (current: {job.status})"}, 409

        # Validate result structure
        status = result_data.get("status")
        if status not in ("completed", "failed"):
            return {"error": "Result 'status' must be 'completed' or 'failed'"}, 400

        # Verify evidence integrity if provided
        evidence_items = result_data.get("evidence", [])
        for item in evidence_items:
            if not isinstance(item, dict):
                return {"error": "Each evidence item must be a JSON object"}, 400

            item_sha = item.get("sha256")
            item_data = item.get("data")
            if item_sha and item_data is not None:
                # Recompute and verify
                canonical = json.dumps(item_data, sort_keys=True, separators=(',', ':'))
                computed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                if computed != item_sha.lower():
                    return {
                        "error": f"Evidence integrity check failed for operation '{item.get('operation_id', '?')}'. "
                                 f"Expected SHA-256 {item_sha}, computed {computed}"
                    }, 400

        # Verify package-level integrity if provided
        integrity = result_data.get("integrity")
        if integrity and isinstance(integrity, dict):
            pkg_hash = integrity.get("hash", "").lower()
            if pkg_hash:
                results_list = result_data.get("results", [])
                canonical_json = json.dumps(results_list, sort_keys=True, separators=(',', ':'))
                computed_pkg = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
                if computed_pkg != pkg_hash:
                    return {
                        "error": f"Package integrity check failed. Expected {pkg_hash}, computed {computed_pkg}"
                    }, 400

        # Transition job
        if status == "completed":
            try:
                job.transition_to(JobStatus.COMPLETED)
            except JobTransitionError as e:
                return {"error": str(e)}, 409
        else:
            try:
                job.transition_to(JobStatus.FAILED, error=result_data.get("error"))
            except JobTransitionError as e:
                return {"error": str(e)}, 409

        # Persist evidence items
        for item in evidence_items:
            evidence = Evidence(
                job_id=job_id,
                agent_id=agent_id,
                operation_id=item.get("operation_id", "unknown"),
                operation_type=item.get("operation_type", "unknown"),
                data=item.get("data", {}),
                sha256=item.get("sha256", ""),
                collected_at=datetime.now(timezone.utc),
                schema_version=item.get("schema_version", "1.0"),
            )
            db.session.add(evidence)

        # Update agent status back to ONLINE
        agent = db.session.get(Agent, agent_id)
        if agent:
            agent.status = "ONLINE"
            agent.current_job = None

        db.session.commit()

        log_event(
            AuditEvent.JOB_COMPLETED if job.status == JobStatus.COMPLETED else AuditEvent.JOB_FAILED,
            agent_id=agent_id,
            job_id=job_id,
            detail=f"Job {job.status.lower()} with {len(evidence_items)} evidence items",
        )

        return {
            "status": "accepted",
            "job_id": job_id,
            "job_status": job.status,
        }, 200

    @classmethod
    def fail_job(cls, job_id: str, agent_id: str, error: str) -> Tuple[Dict[str, Any], int]:
        """Marks a job as FAILED."""
        job = db.session.get(Job, job_id)
        if not job:
            return {"error": f"Job '{job_id}' not found"}, 404

        if job.agent_id != agent_id:
            return {"error": "Unauthorized: agent is not assigned to this job"}, 403

        try:
            job.transition_to(JobStatus.FAILED, error=error)
        except JobTransitionError as e:
            return {"error": str(e)}, 409

        # Update agent status
        agent = db.session.get(Agent, agent_id)
        if agent:
            agent.status = "ONLINE"
            agent.current_job = None

        db.session.commit()

        return {"status": "failed", "job_id": job_id, "error": error}, 200

    @classmethod
    def cancel_job(cls, job_id: str) -> Tuple[Dict[str, Any], int]:
        """Cancels a job (QUEUED or ASSIGNED → CANCELLED)."""
        job = db.session.get(Job, job_id)
        if not job:
            return {"error": f"Job '{job_id}' not found"}, 404

        try:
            job.transition_to(JobStatus.CANCELLED)
        except JobTransitionError as e:
            return {"error": str(e)}, 409

        # Free agent if assigned
        agent = db.session.get(Agent, job.agent_id)
        if agent and agent.current_job == job_id:
            agent.current_job = None
            if agent.status == "BUSY":
                agent.status = "ONLINE"

        db.session.commit()

        log_event(AuditEvent.JOB_CANCELLED, job_id=job_id, detail="Job cancelled")
        return {"status": "cancelled", "job_id": job_id}, 200

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job by ID."""
        job = db.session.get(Job, job_id)
        if not job:
            return None
        result = job.to_dict()
        # Include evidence
        evidence = Evidence.query.filter_by(job_id=job_id).all()
        result["evidence"] = [e.to_dict() for e in evidence]
        return result

    @classmethod
    def list_jobs(
        cls,
        agent_id: Optional[str] = None,
        investigation_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List jobs with optional filters."""
        query = Job.query
        if agent_id:
            query = query.filter_by(agent_id=agent_id)
        if investigation_id:
            query = query.filter_by(investigation_id=investigation_id)
        if status:
            query = query.filter(Job.status.ilike(status))
        jobs = query.order_by(Job.created_at.desc()).all()
        return [j.to_dict() for j in jobs]
