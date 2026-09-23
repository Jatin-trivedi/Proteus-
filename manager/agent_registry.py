"""
Proteus Manager — Agent Registry Service (Priority 6, Phase 2 & Phase 3)

Encapsulates manager-side agent lifecycle, registration validation,
heartbeat processing, stale-agent detection, state management, and database persistence.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

try:
    from models import db, Agent
except ImportError:
    from manager.models import db, Agent

try:
    from runtime.agent.contracts import (
        AgentRegistrationRequest,
        AgentRegistrationResponse,
        ContractValidationError,
        DEFAULT_HEARTBEAT_INTERVAL_SEC,
        OFFLINE_THRESHOLD_SEC,
        VALID_OS_TYPES,
        VALID_HEARTBEAT_STATUSES,
    )
    from runtime.registry import APPROVED_OPERATIONS
except ImportError:
    VALID_OS_TYPES = {"windows", "linux", "darwin", "unix"}
    DEFAULT_HEARTBEAT_INTERVAL_SEC = 30
    OFFLINE_THRESHOLD_SEC = 90
    VALID_HEARTBEAT_STATUSES = {"online", "busy", "error", "offline", "idle"}
    ContractValidationError = ValueError
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

VALID_STATUSES = {"ONLINE", "BUSY", "OFFLINE", "ERROR"}


def _ensure_utc(dt: Optional[Union[datetime, str]]) -> datetime:
    """Safely converts a datetime object or ISO string to timezone-aware UTC datetime."""
    if dt is None:
        return datetime.now(timezone.utc)
    if isinstance(dt, str):
        try:
            # Handle ISO string (including trailing 'Z')
            clean_str = dt.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(clean_str)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return datetime.now(timezone.utc)


class AgentRegistry:
    """Manager-side service managing agent records, heartbeats, and stale detection."""

    @staticmethod
    def generate_stable_agent_id(hostname: str, os_type: str, architecture: str) -> str:
        """Generates a stable, unique agent identifier."""
        raw = f"{hostname.strip().lower()}|{os_type.strip().lower()}|{architecture.strip().lower()}"
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]
        u = uuid.uuid4().hex[:6]
        return f"agent-{h}-{u}"

    @classmethod
    def register_agent(cls, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Validates an agent registration request, creates or updates the agent record,
        sets status=ONLINE, records registered_at and last_heartbeat, and persists to DB.
        """
        if not isinstance(payload, dict):
            return {"error": "Invalid payload format: expected JSON object"}, 400

        hostname = payload.get("hostname")
        os_type = payload.get("os")
        architecture = payload.get("architecture") or payload.get("arch")
        version = payload.get("version", "1.0.0")
        raw_caps = payload.get("capabilities")

        # 1. Validation of required fields
        if not hostname or not isinstance(hostname, str) or not hostname.strip():
            return {"error": "Missing or invalid required field 'hostname'"}, 400

        if not os_type or not isinstance(os_type, str) or not os_type.strip():
            return {"error": "Missing or invalid required field 'os'"}, 400

        os_norm = os_type.strip().lower()
        if not any(os_norm.startswith(valid) for valid in VALID_OS_TYPES):
            return {
                "error": f"Unsupported operating system '{os_type}'. Supported systems: {sorted(VALID_OS_TYPES)}"
            }, 400

        if not architecture or not isinstance(architecture, str) or not architecture.strip():
            return {"error": "Missing or invalid required field 'architecture'"}, 400

        if raw_caps is not None and not isinstance(raw_caps, list):
            return {"error": "Field 'capabilities' must be a list"}, 400

        # Parse capabilities; if empty, populate default approved forensic capabilities
        if not raw_caps:
            capabilities = [{"name": op, "version": "1.0", "enabled": True} for op in sorted(APPROVED_OPERATIONS)]
        else:
            capabilities = []
            for c in raw_caps:
                if isinstance(c, str):
                    capabilities.append({"name": c.strip(), "version": "1.0", "enabled": True})
                elif isinstance(c, dict) and "name" in c:
                    capabilities.append({
                        "name": str(c["name"]).strip(),
                        "version": str(c.get("version", "1.0")),
                        "enabled": bool(c.get("enabled", True)),
                    })
                else:
                    return {"error": f"Invalid capability item format: {c}"}, 400

        # 2. Determine or create agent record
        agent_id = payload.get("agent_id")
        existing_agent = None

        if agent_id:
            existing_agent = db.session.get(Agent, agent_id)

        # If agent_id not provided or not found, check if existing matching hostname & OS
        if not existing_agent:
            if not agent_id:
                agent_id = cls.generate_stable_agent_id(hostname, os_type, architecture)

            agent = Agent(
                agent_id=agent_id,
                hostname=hostname.strip(),
                os=os_norm,
                architecture=architecture.strip(),
                version=version,
                capabilities=capabilities,
                status="ONLINE",
                ip=payload.get("ip", "0.0.0.0"),
            )
            db.session.add(agent)
        else:
            # Duplicate / re-registration: update record
            agent = existing_agent
            agent.hostname = hostname.strip()
            agent.os = os_norm
            agent.architecture = architecture.strip()
            agent.version = version
            agent.capabilities = json.dumps(capabilities)
            agent.status = "ONLINE"
            agent.last_heartbeat = datetime.now(timezone.utc)
            if "ip" in payload:
                agent.ip = payload["ip"]

        db.session.commit()

        return {
            "agent_id": agent.agent_id,
            "agent_token": agent.token,
            "status": "registered",
            "heartbeat_interval": DEFAULT_HEARTBEAT_INTERVAL_SEC,
        }, 200

    @classmethod
    def detect_stale_agents(cls, threshold_seconds: int = OFFLINE_THRESHOLD_SEC) -> List[str]:
        """
        Identifies agents whose last heartbeat exceeds threshold_seconds and marks them OFFLINE.
        Returns list of agent_ids that transitioned to OFFLINE.
        """
        now = datetime.now(timezone.utc)
        active_agents = Agent.query.filter(Agent.status != "OFFLINE").all()
        stale_agent_ids = []

        for agent in active_agents:
            last_hb = _ensure_utc(agent.last_seen)
            elapsed = (now - last_hb).total_seconds()
            if elapsed >= threshold_seconds:
                agent.status = "OFFLINE"
                stale_agent_ids.append(agent.agent_id)

        if stale_agent_ids:
            db.session.commit()

        return stale_agent_ids

    @classmethod
    def get_agent(cls, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve single agent record by ID with stale detection evaluated."""
        cls.detect_stale_agents()
        agent = db.session.get(Agent, agent_id)
        if not agent:
            return None
        return agent.to_dict()

    @classmethod
    def list_agents(cls, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all registered agents with stale detection evaluated."""
        cls.detect_stale_agents()
        query = Agent.query
        if status_filter:
            query = query.filter(Agent.status.ilike(status_filter))
        agents = query.order_by(Agent.registered_at.desc()).all()
        return [a.to_dict() for a in agents]

    @classmethod
    def update_heartbeat(
        cls,
        payload_or_agent_id: Union[Dict[str, Any], str],
        status: Optional[str] = None,
        current_job: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], int]:
        """
        Processes an agent heartbeat request.
        Updates last_heartbeat, status, and current_job.
        Rejects unknown or invalid agents with 404.
        """
        if isinstance(payload_or_agent_id, dict):
            payload = payload_or_agent_id
            agent_id = payload.get("agent_id")
            raw_status = payload.get("status", "ONLINE")
            current_job = payload.get("current_job")
        else:
            agent_id = payload_or_agent_id
            raw_status = status or "ONLINE"

        if not agent_id or not isinstance(agent_id, str) or not agent_id.strip():
            return {"error": "Missing or invalid required field 'agent_id'"}, 400

        # Validate status
        status_norm = str(raw_status).strip().upper() if raw_status else "ONLINE"
        if status_norm == "IDLE":
            status_norm = "ONLINE"

        if status_norm not in VALID_STATUSES:
            return {
                "error": f"Invalid heartbeat status '{raw_status}'. Expected one of {sorted(VALID_STATUSES)}"
            }, 400

        # Validate agent identity in DB
        agent = db.session.get(Agent, agent_id.strip())
        if not agent:
            return {"error": f"Unknown agent: '{agent_id}' is not registered"}, 404

        # Update timestamps and status
        agent.last_seen = datetime.now(timezone.utc)
        agent.status = status_norm
        if current_job is not None:
            agent.current_job = current_job if current_job != "" else None

        db.session.commit()

        return {
            "status": "ok",
            "heartbeat_interval": DEFAULT_HEARTBEAT_INTERVAL_SEC,
            "agent_id": agent.agent_id,
            "agent_status": agent.status,
            "current_job": agent.current_job,
            "server_time": datetime.now(timezone.utc).isoformat(),
        }, 200
