"""
Proteus JOCKY Forensic Runtime — Agent Communication Contract (Priority 6, Phase 1)

Defines strongly-typed, validated data models for agent-manager communication:
- AgentCapability
- AgentRegistrationRequest
- AgentRegistrationResponse
- AgentHeartbeatRequest
- AgentHeartbeatResponse
- AgentTask
- AgentTaskPollResponse
- AgentResultEnvelope
- IntegrityEnvelope

Reuses existing IR models (compiler.ir.model.IRDocument, IROperation)
and runtime result models (runtime.models.OperationResult).
Strictly rejects raw/executable code strings in tasks.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Union

try:
    from compiler.ir.model import IRDocument, IROperation, IRValidationError
except ImportError:
    try:
        from ir.model import IRDocument, IROperation, IRValidationError
    except ImportError:
        IRDocument = None
        IROperation = None
        IRValidationError = ValueError

try:
    from runtime.models import OperationResult
    from runtime.registry import APPROVED_OPERATIONS
except ImportError:
    try:
        from models import OperationResult
        from registry import APPROVED_OPERATIONS
    except ImportError:
        OperationResult = None
        APPROVED_OPERATIONS = {
            "system.info",
            "system.users",
            "processes.list",
            "processes.details",
            "network.interfaces",
            "network.connections",
            "network.routes",
            "network.dns",
            "filesystem.metadata",
            "filesystem.hash",
        }


CONTRACT_SCHEMA_VERSION = "1.0"
DEFAULT_HEARTBEAT_INTERVAL_SEC = 30
OFFLINE_THRESHOLD_SEC = 90
VALID_OS_TYPES = {"windows", "linux", "darwin", "unix"}
VALID_HEARTBEAT_STATUSES = {"online", "busy", "error", "offline", "idle"}
VALID_RESULT_STATUSES = {"completed", "failed"}


class ContractValidationError(ValueError):
    """Raised when an agent contract payload violates schema or semantic constraints."""
    pass


# ==============================================================================
# 1. Agent Capability
# ==============================================================================

@dataclass
class AgentCapability:
    """Represents a forensic capability supported by an agent."""
    name: str
    version: str = "1.0"
    enabled: bool = True

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ContractValidationError("Capability 'name' must be a non-empty string.")
        if not isinstance(self.version, str) or not self.version.strip():
            raise ContractValidationError("Capability 'version' must be a non-empty string.")
        if not isinstance(self.enabled, bool):
            raise ContractValidationError("Capability 'enabled' must be a boolean.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Union[str, Dict[str, Any]]) -> "AgentCapability":
        if isinstance(data, str):
            return cls(name=data.strip())
        if not isinstance(data, dict):
            raise ContractValidationError(f"Expected str or dict for AgentCapability, got {type(data).__name__}.")
        if "name" not in data:
            raise ContractValidationError("Missing required field 'name' in AgentCapability.")
        return cls(
            name=data["name"],
            version=data.get("version", "1.0"),
            enabled=data.get("enabled", True),
        )


# ==============================================================================
# 2. Registration Request & Response
# ==============================================================================

@dataclass
class AgentRegistrationRequest:
    """
    Contract payload for POST /api/v1/agents/register.
    """
    hostname: str
    os: str
    architecture: str
    version: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    agent_id: Optional[str] = None
    ip: Optional[str] = None
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self):
        coerced_caps = []
        for cap in self.capabilities:
            if isinstance(cap, (str, dict)):
                coerced_caps.append(AgentCapability.from_dict(cap))
            elif isinstance(cap, AgentCapability):
                coerced_caps.append(cap)
            else:
                raise ContractValidationError(f"Invalid capability element: {type(cap).__name__}")
        self.capabilities = coerced_caps
        self.validate()

    def validate(self):
        if not isinstance(self.hostname, str) or not self.hostname.strip():
            raise ContractValidationError("Field 'hostname' must be a non-empty string.")

        if not isinstance(self.os, str) or not self.os.strip():
            raise ContractValidationError("Field 'os' must be a non-empty string.")
        os_norm = self.os.strip().lower()
        if not any(os_norm.startswith(valid_os) for valid_os in VALID_OS_TYPES):
            raise ContractValidationError(
                f"Invalid 'os': '{self.os}'. Expected one of {sorted(VALID_OS_TYPES)}."
            )

        if not isinstance(self.architecture, str) or not self.architecture.strip():
            raise ContractValidationError("Field 'architecture' must be a non-empty string.")

        if not isinstance(self.version, str) or not self.version.strip():
            raise ContractValidationError("Field 'version' must be a non-empty string.")

        if not isinstance(self.capabilities, list):
            raise ContractValidationError("Field 'capabilities' must be a list.")

        for cap in self.capabilities:
            if not isinstance(cap, AgentCapability):
                raise ContractValidationError(f"Expected AgentCapability, got {type(cap).__name__}")
            cap.validate()

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "hostname": self.hostname,
            "os": self.os.lower(),
            "architecture": self.architecture,
            "version": self.version,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "schema_version": self.schema_version,
        }
        if self.agent_id:
            d["agent_id"] = self.agent_id
        if self.ip:
            d["ip"] = self.ip
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentRegistrationRequest":
        if not isinstance(data, dict):
            raise ContractValidationError(f"Expected dict for AgentRegistrationRequest, got {type(data).__name__}.")

        required = ["hostname", "os", "architecture", "version"]
        for field_name in required:
            if field_name not in data or data[field_name] is None:
                raise ContractValidationError(f"Missing required field '{field_name}' in registration request.")

        raw_caps = data.get("capabilities", [])
        if not isinstance(raw_caps, list):
            raise ContractValidationError("Field 'capabilities' must be a list.")

        caps = [AgentCapability.from_dict(c) for c in raw_caps]

        return cls(
            hostname=str(data["hostname"]),
            os=str(data["os"]),
            architecture=str(data["architecture"]),
            version=str(data["version"]),
            capabilities=caps,
            agent_id=data.get("agent_id"),
            ip=data.get("ip"),
            schema_version=data.get("schema_version", CONTRACT_SCHEMA_VERSION),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "AgentRegistrationRequest":
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ContractValidationError(f"Invalid JSON in registration request: {e}")
        return cls.from_dict(data)


@dataclass
class AgentRegistrationResponse:
    """
    Contract payload returned by POST /api/v1/agents/register.
    """
    agent_id: str
    status: str = "registered"
    heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL_SEC
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not isinstance(self.agent_id, str) or not self.agent_id.strip():
            raise ContractValidationError("Field 'agent_id' must be a non-empty string.")
        if self.status != "registered":
            raise ContractValidationError(f"Invalid status '{self.status}', expected 'registered'.")
        if not isinstance(self.heartbeat_interval, int) or self.heartbeat_interval <= 0:
            raise ContractValidationError("Field 'heartbeat_interval' must be a positive integer.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "heartbeat_interval": self.heartbeat_interval,
            "schema_version": self.schema_version,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentRegistrationResponse":
        if not isinstance(data, dict):
            raise ContractValidationError(f"Expected dict for AgentRegistrationResponse, got {type(data).__name__}.")
        if "agent_id" not in data or not data["agent_id"]:
            raise ContractValidationError("Missing required field 'agent_id' in registration response.")

        return cls(
            agent_id=str(data["agent_id"]),
            status=data.get("status", "registered"),
            heartbeat_interval=int(data.get("heartbeat_interval", DEFAULT_HEARTBEAT_INTERVAL_SEC)),
            schema_version=data.get("schema_version", CONTRACT_SCHEMA_VERSION),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "AgentRegistrationResponse":
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ContractValidationError(f"Invalid JSON in registration response: {e}")
        return cls.from_dict(data)


# ==============================================================================
# 3. Heartbeat Request & Response
# ==============================================================================

@dataclass
class AgentHeartbeatRequest:
    """
    Contract payload for agent heartbeat polling.
    """
    agent_id: str
    status: str = "online"
    current_job: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = self.status.strip().lower()
        self.validate()

    def validate(self):
        if not isinstance(self.agent_id, str) or not self.agent_id.strip():
            raise ContractValidationError("Field 'agent_id' must be a non-empty string.")

        if self.status not in VALID_HEARTBEAT_STATUSES:
            raise ContractValidationError(
                f"Invalid heartbeat status '{self.status}'. Expected one of {sorted(VALID_HEARTBEAT_STATUSES)}."
            )

        if self.current_job is not None and not isinstance(self.current_job, str):
            raise ContractValidationError("Field 'current_job' must be a string or None.")

        if not isinstance(self.timestamp, str) or not self.timestamp.strip():
            raise ContractValidationError("Field 'timestamp' must be a non-empty ISO format string.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "current_job": self.current_job,
            "timestamp": self.timestamp,
            "schema_version": self.schema_version,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentHeartbeatRequest":
        if not isinstance(data, dict):
            raise ContractValidationError(f"Expected dict for AgentHeartbeatRequest, got {type(data).__name__}.")
        if "agent_id" not in data or not data["agent_id"]:
            raise ContractValidationError("Missing required field 'agent_id' in heartbeat request.")

        return cls(
            agent_id=str(data["agent_id"]),
            status=str(data.get("status", "online")),
            current_job=data.get("current_job"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            schema_version=data.get("schema_version", CONTRACT_SCHEMA_VERSION),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "AgentHeartbeatRequest":
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ContractValidationError(f"Invalid JSON in heartbeat request: {e}")
        return cls.from_dict(data)


# ==============================================================================
# 4. Task & Task Poll Response
# ==============================================================================

@dataclass
class AgentTask:
    """
    Contract payload for an assigned forensic task containing validated IR.
    Reuses IRDocument model. Rejects raw executable source code strings.
    """
    job_id: str
    investigation_id: str
    ir: Union[IRDocument, Dict[str, Any]]
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self):
        # Validate that ir is not a raw code string or arbitrary script
        if isinstance(self.ir, str):
            # Check if it's JSON-serialized IR or raw script code
            raw_str = self.ir.strip()
            if not (raw_str.startswith("{") and raw_str.endswith("}")):
                raise ContractValidationError(
                    "AgentTask rejects executable source code strings. Task must provide structured IRDocument."
                )
            try:
                parsed_json = json.loads(raw_str)
                self.ir = parsed_json
            except json.JSONDecodeError:
                raise ContractValidationError(
                    "AgentTask 'ir' is not a valid JSON IR document."
                )

        if isinstance(self.ir, dict):
            if IRDocument is not None:
                # If dict has investigation or operations
                if "operations" not in self.ir:
                    raise ContractValidationError(
                        "AgentTask 'ir' dict is missing required 'operations' list."
                    )
                # Ensure investigation name is present
                inv_name = self.ir.get("investigation") or self.investigation_id
                ops = self.ir.get("operations", [])
                self.ir = IRDocument(
                    investigation=inv_name,
                    operations=ops,
                    version=self.ir.get("version", "1.0"),
                    ir_type=self.ir.get("ir_type", "jocky_forensic_ir"),
                )

        self.validate()

    def validate(self):
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise ContractValidationError("Field 'job_id' must be a non-empty string.")

        if not isinstance(self.investigation_id, str) or not self.investigation_id.strip():
            raise ContractValidationError("Field 'investigation_id' must be a non-empty string.")

        if IRDocument is not None and isinstance(self.ir, IRDocument):
            self.ir.validate()
        elif isinstance(self.ir, dict):
            if "operations" not in self.ir or not isinstance(self.ir["operations"], list):
                raise ContractValidationError("Field 'ir' must contain an 'operations' list.")
        else:
            raise ContractValidationError(
                f"Field 'ir' must be an IRDocument or valid IR dict, got {type(self.ir).__name__}."
            )

    def to_dict(self) -> Dict[str, Any]:
        ir_dict = self.ir.to_dict() if hasattr(self.ir, "to_dict") else dict(self.ir)
        return {
            "job_id": self.job_id,
            "investigation_id": self.investigation_id,
            "ir": ir_dict,
            "schema_version": self.schema_version,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentTask":
        if not isinstance(data, dict):
            raise ContractValidationError(f"Expected dict for AgentTask, got {type(data).__name__}.")

        job_id = data.get("job_id") or data.get("deploy_id")
        if not job_id:
            raise ContractValidationError("Missing required field 'job_id' in AgentTask.")

        investigation_id = data.get("investigation_id") or data.get("script_id") or "investigation-001"
        if "ir" not in data and "code" in data:
            # Check if 'code' is accidentally raw script code
            code_str = str(data["code"]).strip()
            if not (code_str.startswith("{") and code_str.endswith("}")):
                raise ContractValidationError(
                    "Raw executable script code cannot be accepted as an AgentTask. JOCKY IR required."
                )
            try:
                ir_val = json.loads(code_str)
            except json.JSONDecodeError:
                raise ContractValidationError(
                    "Field 'code' does not contain valid JSON IR data."
                )
        elif "ir" in data:
            ir_val = data["ir"]
        else:
            raise ContractValidationError("Missing required field 'ir' in AgentTask.")

        return cls(
            job_id=str(job_id),
            investigation_id=str(investigation_id),
            ir=ir_val,
            schema_version=data.get("schema_version", CONTRACT_SCHEMA_VERSION),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "AgentTask":
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ContractValidationError(f"Invalid JSON in AgentTask: {e}")
        return cls.from_dict(data)


@dataclass
class AgentHeartbeatResponse:
    """
    Response returned to an agent following a heartbeat / task poll.
    """
    status: str = "ok"
    task: Optional[AgentTask] = None
    heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL_SEC
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self):
        if isinstance(self.task, dict):
            self.task = AgentTask.from_dict(self.task)
        self.validate()

    def validate(self):
        if not isinstance(self.status, str) or not self.status.strip():
            raise ContractValidationError("Field 'status' must be a non-empty string.")
        if self.task is not None:
            if not isinstance(self.task, AgentTask):
                raise ContractValidationError(f"Expected AgentTask, got {type(self.task).__name__}")
            self.task.validate()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "task": self.task.to_dict() if self.task else None,
            "heartbeat_interval": self.heartbeat_interval,
            "schema_version": self.schema_version,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentHeartbeatResponse":
        if not isinstance(data, dict):
            raise ContractValidationError(f"Expected dict for AgentHeartbeatResponse, got {type(data).__name__}.")

        task = None
        if "task" in data and data["task"]:
            task = AgentTask.from_dict(data["task"])
        elif "deployment" in data and data["deployment"]:
            # Backward compatibility with deployment dict
            dep = data["deployment"]
            task = AgentTask.from_dict(dep)

        return cls(
            status=data.get("status", "ok"),
            task=task,
            heartbeat_interval=int(data.get("heartbeat_interval", DEFAULT_HEARTBEAT_INTERVAL_SEC)),
            schema_version=data.get("schema_version", CONTRACT_SCHEMA_VERSION),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "AgentHeartbeatResponse":
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ContractValidationError(f"Invalid JSON in heartbeat response: {e}")
        return cls.from_dict(data)


# Alias for explicit polling semantics
AgentTaskPollResponse = AgentHeartbeatResponse


# ==============================================================================
# 5. Result Envelope & Integrity
# ==============================================================================

@dataclass
class IntegrityEnvelope:
    """Represents a cryptographic digest of forensic results."""
    algorithm: str = "SHA-256"
    hash: str = ""

    def __post_init__(self):
        self.validate()

    def validate(self):
        if self.algorithm != "SHA-256":
            raise ContractValidationError(f"Unsupported algorithm '{self.algorithm}', expected 'SHA-256'.")
        if not isinstance(self.hash, str) or not self.hash.strip():
            raise ContractValidationError("Integrity 'hash' must be a non-empty hex string.")
        if len(self.hash) != 64 or not re.match(r"^[0-9a-fA-F]{64}$", self.hash):
            raise ContractValidationError(
                f"Integrity 'hash' must be a valid 64-character SHA-256 hex string, got '{self.hash}'."
            )

    def to_dict(self) -> Dict[str, str]:
        return {
            "algorithm": self.algorithm,
            "hash": self.hash.lower(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntegrityEnvelope":
        if not isinstance(data, dict):
            raise ContractValidationError(f"Expected dict for IntegrityEnvelope, got {type(data).__name__}.")
        if "hash" not in data:
            raise ContractValidationError("Missing required field 'hash' in IntegrityEnvelope.")
        return cls(
            algorithm=data.get("algorithm", "SHA-256"),
            hash=str(data["hash"]),
        )


@dataclass
class AgentResultEnvelope:
    """
    Contract payload for submitting forensic investigation execution results.
    Guarantees structural validation and SHA-256 cryptographic integrity verification.
    """
    job_id: str
    agent_id: str
    status: str  # "completed" or "failed"
    started_at: str
    completed_at: str
    results: List[Union[OperationResult, Dict[str, Any]]] = field(default_factory=list)
    integrity: Optional[IntegrityEnvelope] = None
    error: Optional[str] = None
    schema_version: str = CONTRACT_SCHEMA_VERSION

    def __post_init__(self):
        # Auto-compute integrity if omitted and results exist
        if self.integrity is None:
            self.integrity = self.compute_integrity()
        elif isinstance(self.integrity, dict):
            self.integrity = IntegrityEnvelope.from_dict(self.integrity)

        self.validate()

    def compute_integrity(self) -> IntegrityEnvelope:
        """Calculates a deterministic SHA-256 hash over serialized results."""
        results_dicts = []
        for r in self.results:
            if hasattr(r, "to_dict"):
                results_dicts.append(r.to_dict())
            elif isinstance(r, dict):
                results_dicts.append(r)
            else:
                results_dicts.append(str(r))

        canonical_json = json.dumps(results_dicts, sort_keys=True, separators=(',', ':'))
        digest = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        return IntegrityEnvelope(algorithm="SHA-256", hash=digest)

    def verify_integrity(self) -> bool:
        """Verifies that the integrity hash matches the current results list."""
        if not self.integrity:
            return False
        expected = self.compute_integrity()
        return self.integrity.hash.lower() == expected.hash.lower()

    def validate(self):
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise ContractValidationError("Field 'job_id' must be a non-empty string.")

        if not isinstance(self.agent_id, str) or not self.agent_id.strip():
            raise ContractValidationError("Field 'agent_id' must be a non-empty string.")

        if self.status not in VALID_RESULT_STATUSES:
            raise ContractValidationError(
                f"Invalid result status '{self.status}'. Expected one of {sorted(VALID_RESULT_STATUSES)}."
            )

        if not isinstance(self.started_at, str) or not self.started_at.strip():
            raise ContractValidationError("Field 'started_at' must be a non-empty ISO format string.")

        if not isinstance(self.completed_at, str) or not self.completed_at.strip():
            raise ContractValidationError("Field 'completed_at' must be a non-empty ISO format string.")

        if not isinstance(self.results, list):
            raise ContractValidationError("Field 'results' must be a list.")

        if self.integrity is not None:
            if not isinstance(self.integrity, IntegrityEnvelope):
                raise ContractValidationError(f"Expected IntegrityEnvelope, got {type(self.integrity).__name__}")
            self.integrity.validate()

    def to_dict(self) -> Dict[str, Any]:
        results_list = []
        for r in self.results:
            if hasattr(r, "to_dict"):
                results_list.append(r.to_dict())
            elif isinstance(r, dict):
                results_list.append(r)
            else:
                results_list.append(str(r))

        d = {
            "job_id": self.job_id,
            "agent_id": self.agent_id,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "results": results_list,
            "integrity": self.integrity.to_dict() if self.integrity else None,
            "schema_version": self.schema_version,
        }
        if self.error:
            d["error"] = self.error
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResultEnvelope":
        if not isinstance(data, dict):
            raise ContractValidationError(f"Expected dict for AgentResultEnvelope, got {type(data).__name__}.")

        required = ["job_id", "agent_id", "status", "started_at", "completed_at"]
        for rf in required:
            if rf not in data or data[rf] is None:
                raise ContractValidationError(f"Missing required field '{rf}' in AgentResultEnvelope.")

        raw_results = data.get("results", [])
        if not isinstance(raw_results, list):
            raise ContractValidationError("Field 'results' must be a list.")

        integrity = None
        if "integrity" in data and data["integrity"]:
            integrity = IntegrityEnvelope.from_dict(data["integrity"])

        return cls(
            job_id=str(data["job_id"]),
            agent_id=str(data["agent_id"]),
            status=str(data["status"]),
            started_at=str(data["started_at"]),
            completed_at=str(data["completed_at"]),
            results=raw_results,
            integrity=integrity,
            error=data.get("error"),
            schema_version=data.get("schema_version", CONTRACT_SCHEMA_VERSION),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "AgentResultEnvelope":
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ContractValidationError(f"Invalid JSON in AgentResultEnvelope: {e}")
        return cls.from_dict(data)
