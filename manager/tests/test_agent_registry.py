"""
Unit and Integration Tests for Manager AgentRegistry and Real Agent Registration (Priority 6, Phase 2)
"""

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import json
import unittest

from app import app
from models import db, Agent
from agent_registry import AgentRegistry


class TestAgentRegistry(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()

    def test_successful_registration(self):
        """Verify successful agent registration persists all fields and returns 200."""
        payload = {
            "hostname": "sec-box-01",
            "os": "linux",
            "architecture": "x86_64",
            "version": "1.0.0",
            "capabilities": [
                {"name": "system.info"},
                {"name": "processes.list"},
            ],
        }

        resp = self.client.post(
            "/api/v1/agents/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("agent_id", data)
        self.assertEqual(data["status"], "registered")
        self.assertEqual(data["heartbeat_interval"], 30)

        agent_id = data["agent_id"]

        # Verify DB record
        with self.app.app_context():
            agent = db.session.get(Agent, agent_id)
            self.assertIsNotNone(agent)
            self.assertEqual(agent.hostname, "sec-box-01")
            self.assertEqual(agent.os, "linux")
            self.assertEqual(agent.architecture, "x86_64")
            self.assertEqual(agent.version, "1.0.0")
            self.assertEqual(agent.status, "ONLINE")
            self.assertIsNotNone(agent.registered_at)
            self.assertIsNotNone(agent.last_heartbeat)
            caps = agent.get_capabilities_list()
            self.assertEqual(len(caps), 2)
            self.assertEqual(caps[0]["name"], "system.info")

    def test_duplicate_registration_behavior(self):
        """Verify that re-registering an agent with the same agent_id updates the record."""
        # 1. Initial registration
        payload1 = {
            "hostname": "sec-box-02",
            "os": "windows",
            "architecture": "x86_64",
            "version": "1.0.0",
            "capabilities": ["system.info"],
        }
        resp1 = self.client.post(
            "/api/v1/agents/register",
            data=json.dumps(payload1),
            content_type="application/json",
        )
        self.assertEqual(resp1.status_code, 200)
        agent_id = resp1.get_json()["agent_id"]

        # 2. Duplicate registration with updated version & capability
        payload2 = {
            "agent_id": agent_id,
            "hostname": "sec-box-02-renamed",
            "os": "windows",
            "architecture": "x86_64",
            "version": "1.1.0",
            "capabilities": ["system.info", "network.interfaces"],
        }
        resp2 = self.client.post(
            "/api/v1/agents/register",
            data=json.dumps(payload2),
            content_type="application/json",
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.get_json()["agent_id"], agent_id)

        # 3. Verify record was updated in place
        with self.app.app_context():
            agent = db.session.get(Agent, agent_id)
            self.assertEqual(agent.hostname, "sec-box-02-renamed")
            self.assertEqual(agent.version, "1.1.0")
            self.assertEqual(agent.status, "ONLINE")
            caps = agent.get_capabilities_list()
            self.assertEqual(len(caps), 2)

    def test_malformed_registration_payloads(self):
        """Verify invalid registration payloads are rejected with 400."""
        # Missing hostname
        resp = self.client.post(
            "/api/v1/agents/register",
            data=json.dumps({"os": "linux", "architecture": "x86_64"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

        # Missing architecture
        resp = self.client.post(
            "/api/v1/agents/register",
            data=json.dumps({"hostname": "box", "os": "linux"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

        # Non-dict JSON
        resp = self.client.post(
            "/api/v1/agents/register",
            data=json.dumps(["not", "an", "object"]),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_unsupported_operating_system(self):
        """Verify unsupported OS returns 400 error."""
        payload = {
            "hostname": "mainframe",
            "os": "solaris_sparc_v9",
            "architecture": "sparc",
            "version": "1.0",
        }
        resp = self.client.post(
            "/api/v1/agents/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Unsupported operating system", resp.get_json()["error"])

    def test_missing_capabilities_defaults(self):
        """Verify registering with omitted capabilities defaults to approved forensic capabilities."""
        payload = {
            "hostname": "default-box",
            "os": "linux",
            "architecture": "arm64",
            "version": "1.0.0",
        }
        resp = self.client.post(
            "/api/v1/agents/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        agent_id = resp.get_json()["agent_id"]

        with self.app.app_context():
            agent = db.session.get(Agent, agent_id)
            caps = agent.get_capabilities_list()
            self.assertEqual(len(caps), 10)  # All 10 approved operations
            names = [c["name"] for c in caps]
            self.assertIn("system.info", names)
            self.assertIn("filesystem.hash", names)

    def test_agent_lookup_by_id(self):
        """Verify GET /api/v1/agents/{agent_id} returns agent details."""
        # 1. Register agent
        payload = {
            "hostname": "lookup-node",
            "os": "linux",
            "architecture": "x86_64",
            "version": "1.0.0",
            "capabilities": ["system.info"],
        }
        reg_resp = self.client.post(
            "/api/v1/agents/register",
            data=json.dumps(payload),
            content_type="application/json",
        )
        agent_id = reg_resp.get_json()["agent_id"]

        # 2. Lookup existing agent
        get_resp = self.client.get(f"/api/v1/agents/{agent_id}")
        self.assertEqual(get_resp.status_code, 200)
        data = get_resp.get_json()
        self.assertEqual(data["agent_id"], agent_id)
        self.assertEqual(data["hostname"], "lookup-node")
        self.assertEqual(data["status"], "ONLINE")
        self.assertIn("registered_at", data)
        self.assertIn("last_heartbeat", data)

        # 3. Lookup non-existent agent returns 404
        bad_resp = self.client.get("/api/v1/agents/agent-non-existent-999")
        self.assertEqual(bad_resp.status_code, 404)

    def test_agent_listing(self):
        """Verify GET /api/v1/agents returns list of all registered agents."""
        # Register two agents
        self.client.post(
            "/api/v1/agents/register",
            data=json.dumps({"hostname": "list-node-1", "os": "linux", "architecture": "x86_64"}),
            content_type="application/json",
        )
        self.client.post(
            "/api/v1/agents/register",
            data=json.dumps({"hostname": "list-node-2", "os": "windows", "architecture": "x86_64"}),
            content_type="application/json",
        )

        list_resp = self.client.get("/api/v1/agents")
        self.assertEqual(list_resp.status_code, 200)
        agents = list_resp.get_json()
        self.assertIsInstance(agents, list)
        self.assertGreaterEqual(len(agents), 2)
        hostnames = [a["hostname"] for a in agents]
        self.assertIn("list-node-1", hostnames)
        self.assertIn("list-node-2", hostnames)


if __name__ == "__main__":
    unittest.main()
