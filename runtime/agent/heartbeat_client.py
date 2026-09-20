"""
Proteus Agent — Real Heartbeat Client and Lifecycle Management (Priority 6, Phase 3)

Implements the client-side heartbeat loop with:
- Automatic registration and agent ID acquisition
- Periodic non-blocking background heartbeat polling
- Graceful network error handling & exponential backoff
- Dynamic status transitions (ONLINE, BUSY, OFFLINE, ERROR)
- Strict security boundary: never executes arbitrary shell commands
- Timezone-safe timestamp generation
"""

from datetime import datetime, timezone
import json
import logging
import platform
import socket
import threading
import time
from typing import Any, Callable, Dict, List, Optional
import urllib.error
import urllib.request

try:
    from runtime.agent.contracts import (
        AgentCapability,
        AgentHeartbeatRequest,
        AgentHeartbeatResponse,
        AgentRegistrationRequest,
        AgentRegistrationResponse,
        DEFAULT_HEARTBEAT_INTERVAL_SEC,
        OFFLINE_THRESHOLD_SEC,
        VALID_HEARTBEAT_STATUSES,
    )
except ImportError:
    DEFAULT_HEARTBEAT_INTERVAL_SEC = 30
    OFFLINE_THRESHOLD_SEC = 90
    VALID_HEARTBEAT_STATUSES = {"online", "busy", "error", "offline", "idle"}

logger = logging.getLogger("proteus.agent.heartbeat")


def get_default_os() -> str:
    s = platform.system().lower()
    if s.startswith("win"):
        return "windows"
    if s.startswith("darwin"):
        return "darwin"
    return "linux"


def get_default_arch() -> str:
    m = platform.machine().lower()
    if m in {"amd64", "x86_64", "x64"}:
        return "x86_64"
    if m in {"arm64", "aarch64"}:
        return "arm64"
    return m or "x86_64"


class AgentHeartbeatClient:
    """
    Manages the lifecycle and heartbeat communications for a Proteus Agent node.
    """

    def __init__(
        self,
        manager_url: str,
        agent_id: Optional[str] = None,
        hostname: Optional[str] = None,
        os_type: Optional[str] = None,
        architecture: Optional[str] = None,
        version: str = "1.0.0",
        capabilities: Optional[List[Any]] = None,
        heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL_SEC,
        offline_threshold: int = OFFLINE_THRESHOLD_SEC,
        base_backoff: float = 1.0,
        max_backoff: float = 60.0,
        http_timeout: float = 10.0,
        on_heartbeat_success: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_heartbeat_error: Optional[Callable[[Exception], None]] = None,
    ):
        self.manager_url = manager_url.rstrip("/")
        self.agent_id = agent_id
        self.hostname = hostname or socket.gethostname()
        self.os_type = (os_type or get_default_os()).lower()
        self.architecture = architecture or get_default_arch()
        self.version = version
        self.capabilities = capabilities or []

        self.heartbeat_interval = max(1, int(heartbeat_interval))
        self.offline_threshold = max(1, int(offline_threshold))
        self.base_backoff = float(base_backoff)
        self.max_backoff = float(max_backoff)
        self.http_timeout = float(http_timeout)

        # Lifecycle & state
        self.status = "ONLINE"
        self.current_job: Optional[str] = None
        self.is_registered: bool = bool(agent_id)
        self.consecutive_failures: int = 0
        self.last_successful_heartbeat: Optional[datetime] = None
        self.last_heartbeat_response: Optional[Dict[str, Any]] = None

        # Threading for non-blocking execution
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Callbacks
        self.on_heartbeat_success = on_heartbeat_success
        self.on_heartbeat_error = on_heartbeat_error

    def _http_post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Performs a synchronous HTTP POST request and parses JSON response."""
        url = f"{self.manager_url}{endpoint}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": f"ProteusAgent/{self.version} ({self.os_type})",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.http_timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if hasattr(e, "read") else ""
            try:
                parsed = json.loads(err_body)
                raise RuntimeError(f"HTTP {e.code}: {parsed.get('error', err_body)}")
            except json.JSONDecodeError:
                raise RuntimeError(f"HTTP {e.code}: {e.reason} - {err_body}")

    def calculate_backoff(self) -> float:
        """Computes exponential backoff delay based on consecutive failure count."""
        if self.consecutive_failures <= 0:
            return 0.0
        exp = min(self.consecutive_failures - 1, 6)
        delay = self.base_backoff * (2 ** exp)
        return min(self.max_backoff, delay)

    def register(self) -> bool:
        """
        Sends registration request to Manager.
        Acquires stable agent_id and configures heartbeat interval.
        """
        payload = {
            "hostname": self.hostname,
            "os": self.os_type,
            "architecture": self.architecture,
            "version": self.version,
            "capabilities": self.capabilities,
        }
        if self.agent_id:
            payload["agent_id"] = self.agent_id

        try:
            # Attempt primary endpoint /api/v1/agents/register, fallback to /api/v1/agent/register
            try:
                resp = self._http_post("/api/v1/agents/register", payload)
            except Exception:
                resp = self._http_post("/api/v1/agent/register", payload)

            with self._lock:
                if "agent_id" in resp:
                    self.agent_id = str(resp["agent_id"])
                    self.is_registered = True
                    if "heartbeat_interval" in resp:
                        self.heartbeat_interval = int(resp["heartbeat_interval"])
                    self.consecutive_failures = 0
                    self.status = "ONLINE"
                    return True
                return False
        except Exception as e:
            with self._lock:
                self.consecutive_failures += 1
            if self.on_heartbeat_error:
                self.on_heartbeat_error(e)
            return False

    def send_heartbeat(self) -> Optional[Dict[str, Any]]:
        """
        Sends a single heartbeat to the Manager.
        Updates status, job state, and records server response.
        """
        if not self.is_registered or not self.agent_id:
            if not self.register():
                return None

        with self._lock:
            current_status = self.status
            current_job = self.current_job
            agent_id = self.agent_id

        payload = {
            "agent_id": agent_id,
            "status": current_status,
            "current_job": current_job,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            try:
                resp = self._http_post("/api/v1/agents/heartbeat", payload)
            except Exception:
                resp = self._http_post("/api/v1/agent/heartbeat", payload)

            with self._lock:
                self.last_successful_heartbeat = datetime.now(timezone.utc)
                self.consecutive_failures = 0
                self.last_heartbeat_response = resp
                if "heartbeat_interval" in resp:
                    self.heartbeat_interval = int(resp["heartbeat_interval"])

            if self.on_heartbeat_success:
                self.on_heartbeat_success(resp)
            return resp

        except Exception as e:
            with self._lock:
                self.consecutive_failures += 1
            if self.on_heartbeat_error:
                self.on_heartbeat_error(e)
            return None

    def transition_to(self, status: str, current_job: Optional[str] = None):
        """Thread-safe status and job transition."""
        norm = status.strip().upper()
        with self._lock:
            self.status = norm
            if current_job is not None:
                self.current_job = current_job if current_job != "" else None

    def set_busy(self, job_id: str):
        """Sets status to BUSY with active job ID."""
        self.transition_to("BUSY", current_job=job_id)

    def set_online(self):
        """Resets status to ONLINE and clears active job."""
        self.transition_to("ONLINE", current_job="")

    def set_error(self, reason: Optional[str] = None):
        """Sets status to ERROR."""
        self.transition_to("ERROR")

    def is_healthy(self) -> bool:
        """Returns True if agent is registered and has communicated within offline threshold."""
        with self._lock:
            if not self.is_registered or not self.last_successful_heartbeat:
                return False
            elapsed = (datetime.now(timezone.utc) - self.last_successful_heartbeat).total_seconds()
            return elapsed < self.offline_threshold

    def _worker_loop(self):
        """Background heartbeat worker loop."""
        while not self._stop_event.is_set():
            if not self.is_registered:
                success = self.register()
                if not success:
                    backoff = self.calculate_backoff()
                    self._stop_event.wait(backoff if backoff > 0 else 2.0)
                    continue

            # Send heartbeat
            resp = self.send_heartbeat()
            if resp is None:
                # Failure: wait backoff
                backoff = self.calculate_backoff()
                self._stop_event.wait(backoff if backoff > 0 else self.heartbeat_interval)
            else:
                # Success: wait standard heartbeat interval
                self._stop_event.wait(self.heartbeat_interval)

    def start(self):
        """Starts the background heartbeat worker thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._worker_loop,
            name=f"ProteusHeartbeatWorker-{self.hostname}",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 5.0):
        """Stops the heartbeat worker cleanly."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            self._thread = None

    def is_running(self) -> bool:
        """Returns True if the background worker thread is active."""
        return bool(self._thread and self._thread.is_alive())
