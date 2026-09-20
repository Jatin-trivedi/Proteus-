"""
Proteus Agent — Main Entry Point (Priority 9)

Starts the full agent: registers, heartbeat, polling loop.
Usage:
    python -m runtime.agent
    PROTEUS_SERVER_URL=http://localhost:5000 python -m runtime.agent
"""

import logging
import os
import signal
import sys
import threading

try:
    from runtime.agent.config import AgentConfig
    from runtime.agent.polling import AgentPollingLoop
except ImportError:
    from agent.config import AgentConfig
    from agent.polling import AgentPollingLoop


def _setup_logging(log_level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def main() -> None:
    config = AgentConfig()
    _setup_logging(config.log_level)

    logger = logging.getLogger("proteus.agent.main")
    logger.info("PROTEUS Agent starting — %r", config)

    loop = AgentPollingLoop(config)

    stop_event = threading.Event()

    def _handle_signal(signum, frame):
        logger.info("Received signal %s — shutting down gracefully…", signum)
        loop.stop()
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        loop.run()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt — stopping agent.")
        loop.stop()

    logger.info("PROTEUS Agent stopped.")


if __name__ == "__main__":
    main()
