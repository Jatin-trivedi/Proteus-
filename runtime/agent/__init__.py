"""
Proteus JOCKY Forensic Runtime — Agent Package

Exports formal communication contracts and types for Priority 6,
plus new Phase 5-9 modules: IR validator, evidence, job executor,
polling loop, and configuration.
"""

from runtime.agent.contracts import (
    AgentCapability,
    AgentRegistrationRequest,
    AgentRegistrationResponse,
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentTask,
    AgentTaskPollResponse,
    AgentResultEnvelope,
    IntegrityEnvelope,
    ContractValidationError,
    CONTRACT_SCHEMA_VERSION,
    DEFAULT_HEARTBEAT_INTERVAL_SEC,
    OFFLINE_THRESHOLD_SEC,
)
from runtime.agent.heartbeat_client import AgentHeartbeatClient
from runtime.agent.ir_validator import validate_ir, AgentIRValidationError
from runtime.agent.evidence import EvidenceItem, EvidencePackage, compute_sha256
from runtime.agent.job_executor import JobExecutor
from runtime.agent.config import AgentConfig
from runtime.agent.polling import AgentPollingLoop

__all__ = [
    # Contracts
    "AgentCapability",
    "AgentRegistrationRequest",
    "AgentRegistrationResponse",
    "AgentHeartbeatRequest",
    "AgentHeartbeatResponse",
    "AgentTask",
    "AgentTaskPollResponse",
    "AgentResultEnvelope",
    "IntegrityEnvelope",
    "ContractValidationError",
    "CONTRACT_SCHEMA_VERSION",
    "DEFAULT_HEARTBEAT_INTERVAL_SEC",
    "OFFLINE_THRESHOLD_SEC",
    # Heartbeat
    "AgentHeartbeatClient",
    # IR Validator
    "validate_ir",
    "AgentIRValidationError",
    # Evidence
    "EvidenceItem",
    "EvidencePackage",
    "compute_sha256",
    # Executor
    "JobExecutor",
    # Config & Polling
    "AgentConfig",
    "AgentPollingLoop",
]

