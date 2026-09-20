"""
Unit and Integration Tests for Priority 6 Agent Communication Contracts (Phase 1)
"""

import json
import unittest

from compiler.ir.model import IRDocument, IROperation
from runtime.agent.contracts import (
    AgentCapability,
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentRegistrationRequest,
    AgentRegistrationResponse,
    AgentResultEnvelope,
    AgentTask,
    AgentTaskPollResponse,
    ContractValidationError,
    IntegrityEnvelope,
)
from runtime.models import OperationResult


class TestAgentContracts(unittest.TestCase):

    # ==========================================================================
    # 1. AgentCapability Tests
    # ==========================================================================

    def test_agent_capability_valid(self):
        cap = AgentCapability(name="network.connections", version="1.0", enabled=True)
        d = cap.to_dict()
        self.assertEqual(d["name"], "network.connections")
        self.assertEqual(d["version"], "1.0")
        self.assertTrue(d["enabled"])

        # From string
        cap2 = AgentCapability.from_dict("system.info")
        self.assertEqual(cap2.name, "system.info")

    def test_agent_capability_invalid(self):
        with self.assertRaises(ContractValidationError):
            AgentCapability(name="")
        with self.assertRaises(ContractValidationError):
            AgentCapability(name="system.info", version="")
        with self.assertRaises(ContractValidationError):
            AgentCapability(name="system.info", enabled="not-a-bool")

    # ==========================================================================
    # 2. AgentRegistrationRequest & Response Tests
    # ==========================================================================

    def test_registration_request_valid(self):
        req = AgentRegistrationRequest(
            hostname="sec-workstation-01",
            os="linux",
            architecture="x86_64",
            version="1.0.0",
            capabilities=[
                AgentCapability(name="system.info"),
                AgentCapability(name="processes.list"),
            ],
        )
        d = req.to_dict()
        self.assertEqual(d["hostname"], "sec-workstation-01")
        self.assertEqual(d["os"], "linux")
        self.assertEqual(d["architecture"], "x86_64")
        self.assertEqual(len(d["capabilities"]), 2)

        # JSON round-trip
        js = req.to_json()
        req_rt = AgentRegistrationRequest.from_json(js)
        self.assertEqual(req_rt.hostname, req.hostname)
        self.assertEqual(req_rt.os, req.os)

    def test_registration_request_validation_rejections(self):
        # Empty hostname
        with self.assertRaises(ContractValidationError):
            AgentRegistrationRequest(
                hostname="", os="windows", architecture="x86_64", version="1.0"
            )
        # Invalid OS
        with self.assertRaises(ContractValidationError):
            AgentRegistrationRequest(
                hostname="node", os="solaris", architecture="sparc", version="1.0"
            )
        # Missing required field in from_dict
        with self.assertRaises(ContractValidationError):
            AgentRegistrationRequest.from_dict({"hostname": "node", "os": "windows"})

    def test_registration_response_valid(self):
        resp = AgentRegistrationResponse(
            agent_id="agent-abc123456789",
            status="registered",
            heartbeat_interval=30,
        )
        d = resp.to_dict()
        self.assertEqual(d["agent_id"], "agent-abc123456789")
        self.assertEqual(d["status"], "registered")
        self.assertEqual(d["heartbeat_interval"], 30)

        # JSON round-trip
        resp_rt = AgentRegistrationResponse.from_json(resp.to_json())
        self.assertEqual(resp_rt.agent_id, resp.agent_id)

    # ==========================================================================
    # 3. AgentHeartbeatRequest & Response Tests
    # ==========================================================================

    def test_heartbeat_request_valid(self):
        hb = AgentHeartbeatRequest(
            agent_id="agent-001",
            status="online",
            current_job=None,
            timestamp="2026-09-21T00:00:00Z",
        )
        d = hb.to_dict()
        self.assertEqual(d["agent_id"], "agent-001")
        self.assertEqual(d["status"], "online")
        self.assertIsNone(d["current_job"])

    def test_heartbeat_request_invalid_status(self):
        with self.assertRaises(ContractValidationError):
            AgentHeartbeatRequest(agent_id="agent-001", status="destroyed")

    def test_heartbeat_response_with_task(self):
        task = AgentTask(
            job_id="job-999",
            investigation_id="inv-123",
            ir=IRDocument(
                investigation="Triage",
                operations=[IROperation(id="op-001", type="system.info")],
            ),
        )
        resp = AgentHeartbeatResponse(
            status="ok",
            task=task,
            heartbeat_interval=30,
        )
        d = resp.to_dict()
        self.assertEqual(d["status"], "ok")
        self.assertIsNotNone(d["task"])
        self.assertEqual(d["task"]["job_id"], "job-999")

        # Round-trip through AgentTaskPollResponse alias
        poll_resp = AgentTaskPollResponse.from_json(resp.to_json())
        self.assertEqual(poll_resp.task.job_id, "job-999")

    # ==========================================================================
    # 4. AgentTask & Rejection of Raw Code
    # ==========================================================================

    def test_agent_task_with_irdocument(self):
        ir = IRDocument(
            investigation="Forensic Analysis",
            operations=[
                IROperation(id="op-001", type="network.interfaces"),
                IROperation(id="op-002", type="filesystem.hash", parameters={"path": "/etc/hosts"}),
            ],
        )
        task = AgentTask(
            job_id="job-101",
            investigation_id="inv-500",
            ir=ir,
        )
        d = task.to_dict()
        self.assertEqual(d["job_id"], "job-101")
        self.assertEqual(len(d["ir"]["operations"]), 2)

        # Reconstruct from dict
        task_rt = AgentTask.from_dict(d)
        self.assertEqual(task_rt.job_id, "job-101")
        self.assertIsInstance(task_rt.ir, IRDocument)

    def test_agent_task_rejects_executable_source_code(self):
        raw_code = "import os; os.system('rm -rf /')"
        with self.assertRaises(ContractValidationError):
            AgentTask(job_id="job-bad", investigation_id="inv-bad", ir=raw_code)

        raw_jocky = 'analysis "Evil" { system.hack(); }'
        with self.assertRaises(ContractValidationError):
            AgentTask.from_dict({
                "job_id": "job-bad",
                "investigation_id": "inv-bad",
                "code": raw_jocky,
            })

    # ==========================================================================
    # 5. AgentResultEnvelope & Integrity Verification
    # ==========================================================================

    def test_result_envelope_integrity_computation_and_verification(self):
        op1 = OperationResult(
            operation_id="op-001",
            type="system.info",
            status="success",
            data={"hostname": "sec-node-1", "os": "Linux"},
        )
        op2 = OperationResult(
            operation_id="op-002",
            type="network.interfaces",
            status="success",
            data={"interfaces": [{"name": "eth0", "addresses": ["10.0.0.5"], "mac": "00:11:22:33:44:55"}]},
        )

        envelope = AgentResultEnvelope(
            job_id="job-101",
            agent_id="agent-999",
            status="completed",
            started_at="2026-09-21T00:00:00Z",
            completed_at="2026-09-21T00:00:02Z",
            results=[op1, op2],
        )

        # Integrity hash is automatically computed
        self.assertIsNotNone(envelope.integrity)
        self.assertEqual(envelope.integrity.algorithm, "SHA-256")
        self.assertTrue(len(envelope.integrity.hash) == 64)
        self.assertTrue(envelope.verify_integrity())

        # Serialize to JSON and parse back
        envelope_rt = AgentResultEnvelope.from_json(envelope.to_json())
        self.assertEqual(envelope_rt.job_id, "job-101")
        self.assertEqual(len(envelope_rt.results), 2)
        self.assertTrue(envelope_rt.verify_integrity())

    def test_result_envelope_detects_tampering(self):
        envelope = AgentResultEnvelope(
            job_id="job-101",
            agent_id="agent-999",
            status="completed",
            started_at="2026-09-21T00:00:00Z",
            completed_at="2026-09-21T00:00:02Z",
            results=[{"op": 1, "data": "original"}],
        )
        self.assertTrue(envelope.verify_integrity())

        # Tamper with results
        envelope.results.append({"op": 2, "data": "tampered"})
        self.assertFalse(envelope.verify_integrity())

    # ==========================================================================
    # 6. Manager API Contract Integration Test
    # ==========================================================================

    def test_manager_api_agents_register_endpoint(self):
        from manager.app import app
        client = app.test_client()

        # POST /api/v1/agents/register with formal contract
        reg_req = {
            "hostname": "test-workstation-007",
            "os": "linux",
            "architecture": "x86_64",
            "version": "1.0.0",
            "capabilities": [
                {"name": "system.info"},
                {"name": "processes.list"},
            ],
        }

        resp = client.post(
            "/api/v1/agents/register",
            data=json.dumps(reg_req),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("agent_id", data)
        self.assertEqual(data["status"], "registered")
        self.assertEqual(data["heartbeat_interval"], 30)

        # Validate with AgentRegistrationResponse contract
        contract_resp = AgentRegistrationResponse.from_dict(data)
        self.assertEqual(contract_resp.status, "registered")
        self.assertEqual(contract_resp.heartbeat_interval, 30)


if __name__ == "__main__":
    unittest.main()
