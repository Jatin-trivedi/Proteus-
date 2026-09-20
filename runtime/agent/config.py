"""
Proteus Agent — Configuration (Priority 9)

Reads agent settings from environment variables.
Never hardcodes credentials. Provides safe defaults.
"""

import os
from typing import Optional


class AgentConfig:
    """Loads agent configuration from environment variables."""

    def __init__(self):
        # Server connection
        self.server_url: str = os.getenv("PROTEUS_SERVER_URL", "http://localhost:5000").rstrip("/")
        self.agent_token: Optional[str] = os.getenv("AGENT_TOKEN")  # set after registration

        # Timing
        self.heartbeat_interval: int = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
        self.poll_interval: int = int(os.getenv("POLL_INTERVAL", "15"))
        self.job_timeout: int = int(os.getenv("JOB_TIMEOUT", "300"))
        self.http_timeout: float = float(os.getenv("HTTP_TIMEOUT", "10.0"))

        # Identity overrides (optional — auto-detected if not set)
        self.hostname: Optional[str] = os.getenv("AGENT_HOSTNAME")
        self.os_type: Optional[str] = os.getenv("AGENT_OS")
        self.architecture: Optional[str] = os.getenv("AGENT_ARCH")
        self.agent_version: str = os.getenv("AGENT_VERSION", "1.0.0")

        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

    def __repr__(self) -> str:
        return (
            f"AgentConfig(server_url={self.server_url!r}, "
            f"poll_interval={self.poll_interval}s, "
            f"heartbeat_interval={self.heartbeat_interval}s, "
            f"job_timeout={self.job_timeout}s)"
        )
