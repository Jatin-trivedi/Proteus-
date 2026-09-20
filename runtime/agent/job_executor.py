"""
Proteus Agent — Job Executor (Priority 8)

Orchestrates the full forensic job execution pipeline:
1. Validate IR (agent-side, double-validation)
2. Execute operations via existing OperationDispatcher (reused, not duplicated)
3. Generate evidence with SHA-256 integrity per operation
4. Build evidence package
5. Return structured AgentResultEnvelope

Security constraints:
- Never executes arbitrary code
- Only approved operations via existing dispatcher
- Configurable timeout with failure isolation
- Failed operations do not crash the executor
"""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional, Tuple

try:
    from runtime.agent.ir_validator import validate_ir, AgentIRValidationError
    from runtime.agent.evidence import EvidenceItem, EvidencePackage
    from runtime.registry import create_default_registry
    from runtime.dispatcher import OperationDispatcher
except ImportError:
    from agent.ir_validator import validate_ir, AgentIRValidationError
    from agent.evidence import EvidenceItem, EvidencePackage
    from registry import create_default_registry
    from dispatcher import OperationDispatcher

logger = logging.getLogger("proteus.agent.executor")

DEFAULT_JOB_TIMEOUT_SEC = 300  # 5 minutes


class JobExecutionError(RuntimeError):
    """Raised when job execution fails at a structural level."""
    pass


class JobExecutor:
    """
    Executes a validated JOCKY IR job using the existing forensic runtime.
    Does NOT implement any forensic collection — reuses OperationDispatcher.
    """

    def __init__(
        self,
        agent_id: str,
        timeout_sec: int = DEFAULT_JOB_TIMEOUT_SEC,
    ):
        self.agent_id = agent_id
        self.timeout_sec = max(1, int(timeout_sec))
        # Create the dispatcher once per executor (reuses existing runtime)
        self._dispatcher = OperationDispatcher(create_default_registry())

    def execute_job(
        self,
        job_id: str,
        investigation_id: str,
        ir: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Executes a forensic job and returns a result dict suitable for upload.

        Pipeline:
          IR dict → agent IR validation → OperationDispatcher → evidence generation
          → EvidencePackage → result dict

        Returns a dict with keys:
          agent_id, status, results, evidence, integrity, error (if failed)
        """
        started_at = datetime.now(timezone.utc).isoformat()

        # Step 1: Agent-side IR validation (second validation after server-side)
        try:
            validate_ir(ir)
        except AgentIRValidationError as e:
            logger.error("Agent IR validation failed for job %s: %s", job_id, e)
            return self._build_failure_result(
                job_id=job_id,
                investigation_id=investigation_id,
                started_at=started_at,
                error=f"IR_VALIDATION_FAILED: {e}",
            )

        # Step 2: Execute operations with timeout
        operations_result = [None]
        execution_error = [None]

        def _run():
            try:
                exec_result = self._dispatcher.dispatch(ir)
                operations_result[0] = exec_result
            except Exception as ex:
                execution_error[0] = ex

        thread = threading.Thread(target=_run, daemon=True, name=f"JobExec-{job_id}")
        thread.start()
        thread.join(timeout=self.timeout_sec)

        if thread.is_alive():
            logger.error("Job %s timed out after %ss", job_id, self.timeout_sec)
            return self._build_failure_result(
                job_id=job_id,
                investigation_id=investigation_id,
                started_at=started_at,
                error=f"JOB_TIMEOUT: execution exceeded {self.timeout_sec}s",
            )

        if execution_error[0] is not None:
            logger.error("Job %s execution error: %s", job_id, execution_error[0])
            return self._build_failure_result(
                job_id=job_id,
                investigation_id=investigation_id,
                started_at=started_at,
                error=f"EXECUTION_ERROR: {execution_error[0]}",
            )

        exec_result = operations_result[0]
        if exec_result is None:
            return self._build_failure_result(
                job_id=job_id,
                investigation_id=investigation_id,
                started_at=started_at,
                error="EXECUTION_ERROR: no result returned",
            )

        completed_at = datetime.now(timezone.utc).isoformat()

        # Step 3: Build serializable operation results
        op_results_list = []
        for op_result in exec_result.results:
            op_results_list.append(op_result.to_dict())

        # Step 4: Generate evidence items per operation
        evidence_items: List[EvidenceItem] = []
        ops_in_ir = ir.get("operations", [])
        op_id_map = {op.get("id"): op.get("type") for op in ops_in_ir if isinstance(op, dict)}

        for op_result in exec_result.results:
            op_id = op_result.operation_id
            op_type = op_result.type
            data = op_result.data if op_result.status == "success" else (
                op_result.error.to_dict() if hasattr(op_result.error, "to_dict")
                else {"error": str(op_result.error)}
            )
            evidence = EvidenceItem.from_operation_result(
                job_id=job_id,
                agent_id=self.agent_id,
                operation_id=op_id,
                operation_type=op_type,
                data=data,
            )
            evidence_items.append(evidence)

        # Step 5: Determine overall job status
        all_succeeded = all(r.get("status") == "success" for r in op_results_list)
        job_status = "completed" if all_succeeded else "completed"  # partial success = completed

        # Step 6: Build evidence package
        package = EvidencePackage.build(
            job_id=job_id,
            agent_id=self.agent_id,
            investigation_id=investigation_id,
            started_at=started_at,
            completed_at=completed_at,
            status=job_status,
            operation_results=op_results_list,
            evidence_items=evidence_items,
        )

        return {
            "agent_id": self.agent_id,
            "status": "completed",
            "started_at": started_at,
            "completed_at": completed_at,
            "results": op_results_list,
            "evidence": [e.to_dict() for e in evidence_items],
            "integrity": {
                "algorithm": "SHA-256",
                "hash": package.package_hash,
            },
        }

    def _build_failure_result(
        self,
        job_id: str,
        investigation_id: str,
        started_at: str,
        error: str,
    ) -> Dict[str, Any]:
        """Builds a structured failure result dict."""
        completed_at = datetime.now(timezone.utc).isoformat()
        return {
            "agent_id": self.agent_id,
            "status": "failed",
            "started_at": started_at,
            "completed_at": completed_at,
            "results": [],
            "evidence": [],
            "error": error,
            "integrity": {
                "algorithm": "SHA-256",
                "hash": "",
            },
        }
