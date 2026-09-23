"""
Proteus Agent — Polling Loop (Priority 9)

Implements the main agent polling loop:

  while running:
      heartbeat()
      job = poll_for_job()
      if job:
          ack_job(job)
          execute_job(job)
          upload_results(job)
      sleep(POLL_INTERVAL)

Features:
- Graceful shutdown via threading.Event
- Retry with exponential backoff on network failure
- Network error isolation (doesn't crash the loop)
- Non-blocking heartbeat (separate thread or inline)
- Configurable poll interval
"""

from datetime import datetime, timezone
import json
import logging
import platform
import socket
import threading
import time
from typing import Any, Dict, Optional
import urllib.error
import urllib.request

try:
    from runtime.agent.config import AgentConfig
    from runtime.agent.job_executor import JobExecutor
except ImportError:
    from agent.config import AgentConfig
    from agent.job_executor import JobExecutor

logger = logging.getLogger("proteus.agent.polling")


def _http_request(
    url: str,
    method: str = "GET",
    payload: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Performs a simple HTTP request and returns parsed JSON."""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if hasattr(e, "read") else ""
        try:
            parsed = json.loads(err_body)
            raise RuntimeError(f"HTTP {e.code}: {parsed.get('error', err_body)}")
        except json.JSONDecodeError:
            raise RuntimeError(f"HTTP {e.code}: {e.reason}")


class AgentPollingLoop:
    """
    Main agent polling loop. Manages heartbeat and job polling,
    delegating execution to JobExecutor.
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id: Optional[str] = None
        self.agent_token: Optional[str] = config.agent_token

        self._stop_event = threading.Event()
        self._consecutive_failures = 0
        self._base_backoff = 1.0
        self._max_backoff = 60.0
        self._lock = threading.Lock()

        self._executor = JobExecutor(
            agent_id="",  # set after registration
            timeout_sec=config.job_timeout,
        )

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------

    def _get_agent_info(self) -> Dict[str, Any]:
        """Gathers agent identification info for registration."""
        system = platform.system().lower()
        if system.startswith("win"):
            os_type = "windows"
        elif system.startswith("darwin"):
            os_type = "darwin"
        else:
            os_type = "linux"

        machine = platform.machine().lower()
        if machine in {"amd64", "x86_64", "x64"}:
            arch = "x86_64"
        elif machine in {"arm64", "aarch64"}:
            arch = "arm64"
        else:
            arch = machine or "x86_64"

        return {
            "hostname": self.config.hostname or socket.gethostname(),
            "os": self.config.os_type or os_type,
            "architecture": self.config.architecture or arch,
            "version": self.config.agent_version,
        }

    def register(self) -> bool:
        """Registers with the manager and stores agent_id and token."""
        info = self._get_agent_info()
        url = f"{self.config.server_url}/api/v1/agent/register"
        try:
            resp = _http_request(url, method="POST", payload=info, timeout=self.config.http_timeout)
            if "agent_id" in resp:
                with self._lock:
                    self.agent_id = resp["agent_id"]
                    # Server returns token once on registration
                    if "agent_token" in resp:
                        self.agent_token = resp["agent_token"]
                    # Update executor with real agent_id
                    self._executor = JobExecutor(
                        agent_id=self.agent_id,
                        timeout_sec=self.config.job_timeout,
                    )
                    self._consecutive_failures = 0
                logger.info("Registered as agent %s", self.agent_id)
                return True
            logger.error("Registration response missing 'agent_id': %s", resp)
            return False
        except Exception as e:
            logger.warning("Registration failed: %s", e)
            self._consecutive_failures += 1
            return False

    # -------------------------------------------------------------------------
    # Heartbeat
    # -------------------------------------------------------------------------

    def _send_heartbeat(self, status: str = "online") -> bool:
        """Sends a heartbeat to the manager."""
        if not self.agent_id:
            return False
        url = f"{self.config.server_url}/api/v1/agent/heartbeat"
        payload = {
            "agent_id": self.agent_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            _http_request(url, method="POST", payload=payload, timeout=self.config.http_timeout)
            return True
        except Exception as e:
            logger.warning("Heartbeat failed: %s", e)
            return False

    # -------------------------------------------------------------------------
    # Job Polling
    # -------------------------------------------------------------------------

    def _poll_for_job(self) -> Optional[Dict[str, Any]]:
        """Polls the manager for the next available job."""
        if not self.agent_id or not self.agent_token:
            return None
        url = f"{self.config.server_url}/api/v1/agents/{self.agent_id}/jobs/next"
        try:
            resp = _http_request(
                url, method="GET", token=self.agent_token,
                timeout=self.config.http_timeout,
            )
            return resp.get("job")  # None if no job available
        except Exception as e:
            logger.warning("Job poll failed: %s", e)
            return None

    def _acknowledge_job(self, job_id: str) -> bool:
        """Acknowledges job receipt — transitions ASSIGNED → RUNNING on server."""
        if not self.agent_id or not self.agent_token:
            return False
        url = f"{self.config.server_url}/api/v1/jobs/{job_id}/ack"
        payload = {"agent_id": self.agent_id}
        try:
            resp = _http_request(
                url, method="POST", payload=payload, token=self.agent_token,
                timeout=self.config.http_timeout,
            )
            return resp.get("status") == "acknowledged"
        except Exception as e:
            logger.error("Job acknowledgement failed for %s: %s", job_id, e)
            return False

    def _upload_results(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Uploads forensic results to the manager."""
        if not self.agent_id or not self.agent_token:
            return False
        url = f"{self.config.server_url}/api/v1/jobs/{job_id}/results"
        payload = {
            "agent_id": self.agent_id,
            **result,
        }
        try:
            _http_request(
                url, method="POST", payload=payload, token=self.agent_token,
                timeout=self.config.http_timeout,
            )
            logger.info("Results uploaded for job %s", job_id)
            return True
        except Exception as e:
            logger.error("Result upload failed for %s: %s", job_id, e)
            return False

    # -------------------------------------------------------------------------
    # Backoff
    # -------------------------------------------------------------------------

    def _backoff_sleep(self) -> None:
        """Sleeps for exponentially increasing intervals on consecutive failures."""
        failures = self._consecutive_failures
        if failures <= 0:
            return
        exp = min(failures - 1, 6)
        delay = min(self._base_backoff * (2 ** exp), self._max_backoff)
        logger.debug("Backoff sleep %.1fs (failures=%d)", delay, failures)
        self._stop_event.wait(delay)

    # -------------------------------------------------------------------------
    # Main Loop
    # -------------------------------------------------------------------------

    def run(self) -> None:
        """
        Main polling loop. Blocks until stop() is called.
        Handles registration, heartbeat, polling, execution, and result upload.
        """
        logger.info("Agent polling loop starting. Server: %s", self.config.server_url)

        # Ensure registered
        while not self._stop_event.is_set() and not self.agent_id:
            if not self.register():
                self._backoff_sleep()
            else:
                break

        while not self._stop_event.is_set():
            try:
                # Heartbeat
                self._send_heartbeat()

                # Poll for job
                job = self._poll_for_job()

                if job:
                    job_id = job.get("job_id")
                    investigation_id = job.get("investigation_id", "unknown")
                    ir = job.get("ir", {})

                    logger.info("Received job %s for investigation %s", job_id, investigation_id)

                    # Acknowledge
                    if not self._acknowledge_job(job_id):
                        logger.warning("Failed to ack job %s, skipping", job_id)
                        self._consecutive_failures += 1
                        self._backoff_sleep()
                        continue

                    # Execute
                    logger.info("Executing job %s", job_id)
                    result = self._executor.execute_job(
                        job_id=job_id,
                        investigation_id=investigation_id,
                        ir=ir,
                    )

                    # Upload
                    self._upload_results(job_id, result)
                    self._consecutive_failures = 0

                else:
                    self._consecutive_failures = 0

                # Wait before next poll (interruptible)
                self._stop_event.wait(self.config.poll_interval)

            except Exception as e:
                logger.error("Polling loop error: %s", e)
                self._consecutive_failures += 1
                self._backoff_sleep()

        logger.info("Agent polling loop stopped.")

    def stop(self) -> None:
        """Signals the polling loop to stop gracefully."""
        self._stop_event.set()

    def start_background(self) -> threading.Thread:
        """Starts the polling loop in a background daemon thread."""
        t = threading.Thread(target=self.run, name="ProteusPollingLoop", daemon=True)
        t.start()
        return t
