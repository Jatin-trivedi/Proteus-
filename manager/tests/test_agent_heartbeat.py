"""
Unit and Integration Tests for Priority 6, Phase 3: Real Agent Heartbeat Lifecycle
"""

from datetime import datetime, timedelta, timezone
import json
import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app
from models import db, Agent
from agent_registry import AgentRegistry, OFFLINE_THRESHOLD_SEC
from runtime.agent.heartbeat_client import AgentHeartbeatClient


class TestAgentHeartbeatLifecycle(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()

    def _register_test_agent(self, hostname="test-agent-node", os_type="linux", arch="x86_64"):
        """Helper to register an agent and return its agent_id."""
        payload = {
            "hostname": hostname,
            "os": os_type,
            "architecture": arch,
            "version": "1.0.0",
            "capabilities": ["system.info"],
        }
        resp = self.client.post(
            "/api/v1/agents/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        return resp.get_json()["agent_id"]

    # ==========================================================================
    # 1. Heartbeat Success Test
    # ==========================================================================

    def test_heartbeat_success(self):
        """Verify that a valid agent heartbeat updates last_heartbeat, status, and current_job."""
        agent_id = self._register_test_agent(hostname="hb-node-01")

        # Initial state verification
        with self.app.app_context():
            agent = db.session.get(Agent, agent_id)
            initial_last_seen = agent.last_seen

        time.sleep(0.01)

        payload = {
            "agent_id": agent_id,
            "status": "ONLINE",
            "current_job": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        resp = self.client.post(
            "/api/v1/agents/heartbeat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["heartbeat_interval"], 30)
        self.assertEqual(data["agent_id"], agent_id)
        self.assertEqual(data["agent_status"], "ONLINE")

        with self.app.app_context():
            agent = db.session.get(Agent, agent_id)
            self.assertEqual(agent.status, "ONLINE")
            self.assertIsNone(agent.current_job)
            self.assertGreaterEqual(agent.last_seen, initial_last_seen)

    # ==========================================================================
    # 2. Unknown Agent Rejection Test
    # ==========================================================================

    def test_unknown_agent_rejection(self):
        """Verify that sending a heartbeat from an unknown/unregistered agent returns 404."""
        payload = {
            "agent_id": "agent-non-existent-9999",
            "status": "ONLINE",
        }

        resp = self.client.post(
            "/api/v1/agents/heartbeat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("Unknown agent", data["error"])

    # ==========================================================================
    # 3. Stale Agent Detection Test
    # ==========================================================================

    def test_stale_agent_detection(self):
        """Verify that agents with last_heartbeat older than 90 seconds are marked OFFLINE."""
        agent_id = self._register_test_agent(hostname="stale-node-01")

        # Manually backdate the agent's last_seen to 120 seconds in the past
        with self.app.app_context():
            agent = db.session.get(Agent, agent_id)
            past_time = datetime.now(timezone.utc) - timedelta(seconds=120)
            agent.last_seen = past_time
            agent.status = "ONLINE"
            db.session.commit()

        # Run stale detection
        with self.app.app_context():
            stale_ids = AgentRegistry.detect_stale_agents(threshold_seconds=90)
            self.assertIn(agent_id, stale_ids)

            # Check agent status
            agent = db.session.get(Agent, agent_id)
            self.assertEqual(agent.status, "OFFLINE")

        # Verify listing agents also reflects OFFLINE
        resp = self.client.get(f"/api/v1/agents/{agent_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "OFFLINE")

    # ==========================================================================
    # 4. Heartbeat Recovery Test
    # ==========================================================================

    def test_heartbeat_recovery(self):
        """Verify that an agent marked OFFLINE transitions back to ONLINE upon sending heartbeat."""
        agent_id = self._register_test_agent(hostname="recovery-node-01")

        # Mark agent OFFLINE
        with self.app.app_context():
            agent = db.session.get(Agent, agent_id)
            agent.status = "OFFLINE"
            agent.last_seen = datetime.now(timezone.utc) - timedelta(seconds=300)
            db.session.commit()

        # Verify agent is OFFLINE
        resp_check = self.client.get(f"/api/v1/agents/{agent_id}")
        self.assertEqual(resp_check.get_json()["status"], "OFFLINE")

        # Send recovery heartbeat
        payload = {
            "agent_id": agent_id,
            "status": "ONLINE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        resp = self.client.post(
            "/api/v1/agents/heartbeat",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # Verify agent is restored to ONLINE
        with self.app.app_context():
            agent = db.session.get(Agent, agent_id)
            self.assertEqual(agent.status, "ONLINE")

    # ==========================================================================
    # 5. Status Transitions Test
    # ==========================================================================

    def test_status_transitions(self):
        """Verify valid status transitions (ONLINE -> BUSY -> ERROR -> ONLINE) and rejection of invalid status."""
        agent_id = self._register_test_agent(hostname="status-test-node")

        # Transition to BUSY with current_job
        resp_busy = self.client.post(
            "/api/v1/agents/heartbeat",
            data=json.dumps({
                "agent_id": agent_id,
                "status": "BUSY",
                "current_job": "job-investigation-42",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp_busy.status_code, 200)
        with self.app.app_context():
            agent = db.session.get(Agent, agent_id)
            self.assertEqual(agent.status, "BUSY")
            self.assertEqual(agent.current_job, "job-investigation-42")

        # Transition to ERROR
        resp_err = self.client.post(
            "/api/v1/agents/heartbeat",
            data=json.dumps({
                "agent_id": agent_id,
                "status": "ERROR",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp_err.status_code, 200)
        with self.app.app_context():
            agent = db.session.get(Agent, agent_id)
            self.assertEqual(agent.status, "ERROR")

        # Transition back to ONLINE
        resp_online = self.client.post(
            "/api/v1/agents/heartbeat",
            data=json.dumps({
                "agent_id": agent_id,
                "status": "ONLINE",
                "current_job": None,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp_online.status_code, 200)
        with self.app.app_context():
            agent = db.session.get(Agent, agent_id)
            self.assertEqual(agent.status, "ONLINE")

        # Rejection of invalid status
        resp_invalid = self.client.post(
            "/api/v1/agents/heartbeat",
            data=json.dumps({
                "agent_id": agent_id,
                "status": "MALICIOUS_STATUS",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp_invalid.status_code, 400)
        self.assertIn("Invalid heartbeat status", resp_invalid.get_json()["error"])

    # ==========================================================================
    # 6. Agent Client Network Failure & Exponential Backoff Test
    # ==========================================================================

    def test_agent_client_network_failure_and_backoff(self):
        """Verify that AgentHeartbeatClient handles connection failures and computes exponential backoff."""
        client = AgentHeartbeatClient(
            manager_url="http://127.0.0.1:59999",  # Non-existent server
            hostname="backoff-agent",
            base_backoff=1.0,
            max_backoff=16.0,
            http_timeout=0.2,
        )

        self.assertEqual(client.consecutive_failures, 0)
        self.assertEqual(client.calculate_backoff(), 0.0)

        # Attempt 1 -> failure
        success = client.register()
        self.assertFalse(success)
        self.assertEqual(client.consecutive_failures, 1)
        self.assertEqual(client.calculate_backoff(), 1.0)

        # Attempt 2 -> failure
        client.register()
        self.assertEqual(client.consecutive_failures, 2)
        self.assertEqual(client.calculate_backoff(), 2.0)

        # Attempt 3 -> failure
        client.register()
        self.assertEqual(client.consecutive_failures, 3)
        self.assertEqual(client.calculate_backoff(), 4.0)

        # Attempt 4 -> failure
        client.register()
        self.assertEqual(client.consecutive_failures, 4)
        self.assertEqual(client.calculate_backoff(), 8.0)

        # Attempt 5 -> failure (capped at max_backoff=16.0)
        client.register()
        client.register()
        self.assertEqual(client.calculate_backoff(), 16.0)

    # ==========================================================================
    # 7. Agent Client Non-Blocking Thread Lifecycle & Status Test
    # ==========================================================================

    def test_agent_client_lifecycle_and_non_blocking(self):
        """Verify AgentHeartbeatClient starts background worker, sends heartbeat, and stops cleanly."""
        agent_id = self._register_test_agent(hostname="lifecycle-client-node")

        client = AgentHeartbeatClient(
            manager_url="http://localhost:5000",
            agent_id=agent_id,
            hostname="lifecycle-client-node",
            heartbeat_interval=30,
        )

        # Mock _http_post to return success without making real network call
        client._http_post = MagicMock(return_value={"status": "ok", "heartbeat_interval": 30, "agent_id": agent_id})

        # Test single heartbeat
        resp = client.send_heartbeat()
        self.assertIsNotNone(resp)
        self.assertEqual(resp["status"], "ok")
        self.assertTrue(client.is_healthy())

        # Test status transition methods
        client.set_busy("job-100")
        self.assertEqual(client.status, "BUSY")
        self.assertEqual(client.current_job, "job-100")

        client.set_online()
        self.assertEqual(client.status, "ONLINE")
        self.assertIsNone(client.current_job)

        client.set_error("Collector timeout")
        self.assertEqual(client.status, "ERROR")

        # Test non-blocking background thread start and clean stop
        client.start()
        self.assertTrue(client.is_running())
        time.sleep(0.05)
        client.stop(timeout=1.0)
        self.assertFalse(client.is_running())
