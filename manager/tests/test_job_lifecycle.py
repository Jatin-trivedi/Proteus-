"""
Manager-side tests for job lifecycle, IR validation, evidence, and auth (Phase 14).

Tests:
1. Job creation with valid IR
2. Job creation with invalid IR (various failure modes)
3. Job state machine transitions
4. Atomic job claiming / polling
5. Job acknowledgement
6. Wrong-agent ACK rejected
7. Job cancellation
8. Job listing/retrieval
9. Result upload with valid evidence
10. Wrong-agent result upload rejected
11. Evidence SHA-256 verification
12. Job not RUNNING → result rejected
13. Agent token auth on protected endpoints
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pytest

from app import create_app
from models import db, Agent, Job, JobStatus, JobTransitionError, Investigation


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def registered_agent(app):
    """Creates a registered agent and returns its dict (agent_id, token)."""
    with app.app_context():
        agent = Agent(
            agent_id="agent-test-001",
            hostname="test-host",
            os="linux",
            architecture="x86_64",
            version="1.0.0",
        )
        db.session.add(agent)
        db.session.commit()
        token = agent.token
        return {"agent_id": "agent-test-001", "token": token}


@pytest.fixture
def registered_agent2(app):
    """Creates a second registered agent."""
    with app.app_context():
        agent = Agent(
            agent_id="agent-test-002",
            hostname="test-host-2",
            os="windows",
            architecture="amd64",
            version="1.0.0",
        )
        db.session.add(agent)
        db.session.commit()
        token = agent.token
        return {"agent_id": "agent-test-002", "token": token}


@pytest.fixture
def investigation(app):
    """Creates a test investigation."""
    with app.app_context():
        inv = Investigation(name="Test Investigation", investigation_id="INV-TEST-001")
        db.session.add(inv)
        db.session.commit()
        return inv.to_dict()


VALID_IR = {
    "version": "1.0",
    "ir_type": "jocky_forensic_ir",
    "investigation": "Test Investigation",
    "operations": [
        {"id": "op-001", "type": "system.info", "parameters": {}},
        {"id": "op-002", "type": "network.connections", "parameters": {}},
    ],
}


# ── Job Creation ──────────────────────────────────────────────────────────────

class TestJobCreation:
    def test_create_job_valid_ir(self, client, registered_agent, investigation, app):
        """Valid IR creates a job successfully."""
        with app.app_context():
            resp = client.post("/api/v1/jobs", json={
                "agent_id": "agent-test-001",
                "investigation_id": "INV-TEST-001",
                "ir": VALID_IR,
            })
        assert resp.status_code == 201
        data = resp.get_json()
        assert "job_id" in data
        assert data["agent_id"] == "agent-test-001"
        assert data["status"] == "ASSIGNED"

    def test_create_job_missing_ir(self, client, registered_agent, investigation, app):
        """Missing IR field returns 400."""
        with app.app_context():
            resp = client.post("/api/v1/jobs", json={
                "agent_id": "agent-test-001",
                "investigation_id": "INV-TEST-001",
            })
        assert resp.status_code == 400

    def test_create_job_unknown_operation_rejected(self, client, registered_agent, investigation, app):
        """IR with unknown operation type is rejected."""
        bad_ir = {**VALID_IR, "operations": [
            {"id": "op-001", "type": "evil.command", "parameters": {}},
        ]}
        with app.app_context():
            resp = client.post("/api/v1/jobs", json={
                "agent_id": "agent-test-001",
                "investigation_id": "INV-TEST-001",
                "ir": bad_ir,
            })
        assert resp.status_code == 400
        assert "unapproved" in resp.get_json().get("error", "")

    def test_create_job_missing_version_rejected(self, client, registered_agent, investigation, app):
        """IR missing version is rejected."""
        bad_ir = {k: v for k, v in VALID_IR.items() if k != "version"}
        with app.app_context():
            resp = client.post("/api/v1/jobs", json={
                "agent_id": "agent-test-001",
                "investigation_id": "INV-TEST-001",
                "ir": bad_ir,
            })
        assert resp.status_code == 400

    def test_create_job_duplicate_operation_ids_rejected(self, client, registered_agent, investigation, app):
        """IR with duplicate operation IDs is rejected."""
        bad_ir = {**VALID_IR, "operations": [
            {"id": "op-001", "type": "system.info", "parameters": {}},
            {"id": "op-001", "type": "network.connections", "parameters": {}},
        ]}
        with app.app_context():
            resp = client.post("/api/v1/jobs", json={
                "agent_id": "agent-test-001",
                "investigation_id": "INV-TEST-001",
                "ir": bad_ir,
            })
        assert resp.status_code == 400

    def test_create_job_forbidden_field_rejected(self, client, registered_agent, investigation, app):
        """IR with forbidden 'code' field is rejected."""
        bad_ir = {**VALID_IR, "operations": [
            {"id": "op-001", "type": "system.info", "code": "import os"},
        ]}
        with app.app_context():
            resp = client.post("/api/v1/jobs", json={
                "agent_id": "agent-test-001",
                "investigation_id": "INV-TEST-001",
                "ir": bad_ir,
            })
        assert resp.status_code == 400

    def test_create_job_unknown_agent_returns_404(self, client, investigation, app):
        """Unknown agent_id returns 404."""
        with app.app_context():
            resp = client.post("/api/v1/jobs", json={
                "agent_id": "ghost-agent",
                "investigation_id": "INV-TEST-001",
                "ir": VALID_IR,
            })
        assert resp.status_code == 404


# ── Job Polling ───────────────────────────────────────────────────────────────

class TestJobPolling:
    def _create_job(self, app, agent_id="agent-test-001", inv_id="INV-TEST-001"):
        with app.app_context():
            job = Job(agent_id=agent_id, investigation_id=inv_id, ir=VALID_IR)
            job.transition_to(JobStatus.ASSIGNED)
            db.session.add(job)
            db.session.commit()
            return job.job_id

    def test_poll_returns_job_when_available(self, client, registered_agent, investigation, app):
        """Polling returns an ASSIGNED job for the agent."""
        job_id = self._create_job(app)
        with app.app_context():
            resp = client.get(
                "/api/v1/agents/agent-test-001/jobs/next",
                headers={"Authorization": f"Bearer {registered_agent['token']}"},
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["job"] is not None
        assert data["job"]["job_id"] == job_id

    def test_poll_returns_null_when_no_jobs(self, client, registered_agent, investigation, app):
        """Polling returns null job when no jobs available."""
        with app.app_context():
            resp = client.get(
                "/api/v1/agents/agent-test-001/jobs/next",
                headers={"Authorization": f"Bearer {registered_agent['token']}"},
            )
        assert resp.status_code == 200
        assert resp.get_json()["job"] is None

    def test_poll_requires_auth(self, client, registered_agent, investigation, app):
        """Polling without token returns 401."""
        with app.app_context():
            resp = client.get("/api/v1/agents/agent-test-001/jobs/next")
        assert resp.status_code == 401

    def test_poll_wrong_agent_rejected(self, client, registered_agent, registered_agent2, investigation, app):
        """Agent A cannot poll Agent B's jobs."""
        self._create_job(app, agent_id="agent-test-002")
        with app.app_context():
            # Agent 1 token, but requesting agent 2's jobs
            resp = client.get(
                "/api/v1/agents/agent-test-002/jobs/next",
                headers={"Authorization": f"Bearer {registered_agent['token']}"},
            )
        assert resp.status_code == 403


# ── Job Acknowledgement ───────────────────────────────────────────────────────

class TestJobAcknowledgement:
    def _create_assigned_job(self, app, agent_id="agent-test-001"):
        with app.app_context():
            job = Job(agent_id=agent_id, investigation_id="INV-TEST-001", ir=VALID_IR)
            job.transition_to(JobStatus.ASSIGNED)
            db.session.add(job)
            db.session.commit()
            return job.job_id

    def test_ack_transitions_to_running(self, client, registered_agent, investigation, app):
        """Successful ACK transitions ASSIGNED → RUNNING."""
        job_id = self._create_assigned_job(app)
        with app.app_context():
            resp = client.post(
                f"/api/v1/jobs/{job_id}/ack",
                json={"agent_id": "agent-test-001"},
                headers={"Authorization": f"Bearer {registered_agent['token']}"},
            )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "acknowledged"

    def test_ack_requires_auth(self, client, registered_agent, investigation, app):
        """ACK without token returns 401."""
        job_id = self._create_assigned_job(app)
        with app.app_context():
            resp = client.post(f"/api/v1/jobs/{job_id}/ack", json={"agent_id": "agent-test-001"})
        assert resp.status_code == 401

    def test_ack_wrong_agent_rejected(self, client, registered_agent, registered_agent2, investigation, app):
        """Agent B cannot ACK Agent A's job."""
        job_id = self._create_assigned_job(app, agent_id="agent-test-001")
        with app.app_context():
            resp = client.post(
                f"/api/v1/jobs/{job_id}/ack",
                json={"agent_id": "agent-test-002"},
                headers={"Authorization": f"Bearer {registered_agent2['token']}"},
            )
        assert resp.status_code == 403

    def test_ack_nonexistent_job_returns_404(self, client, registered_agent, app):
        """ACK on non-existent job returns 404."""
        with app.app_context():
            resp = client.post(
                "/api/v1/jobs/ghost-job/ack",
                json={"agent_id": "agent-test-001"},
                headers={"Authorization": f"Bearer {registered_agent['token']}"},
            )
        assert resp.status_code == 404


# ── Job State Machine ─────────────────────────────────────────────────────────

class TestJobStateMachine:
    def test_queued_to_assigned(self, app):
        """QUEUED → ASSIGNED is valid."""
        with app.app_context():
            job = Job(agent_id="agent-test-001", investigation_id="INV-001", ir=VALID_IR)
            assert job.status == JobStatus.QUEUED
            job.transition_to(JobStatus.ASSIGNED)
            assert job.status == JobStatus.ASSIGNED

    def test_assigned_to_running(self, app):
        """ASSIGNED → RUNNING is valid."""
        with app.app_context():
            job = Job(agent_id="agent-test-001", investigation_id="INV-001", ir=VALID_IR)
            job.transition_to(JobStatus.ASSIGNED)
            job.transition_to(JobStatus.RUNNING)
            assert job.status == JobStatus.RUNNING
            assert job.started_at is not None

    def test_running_to_completed(self, app):
        """RUNNING → COMPLETED is valid."""
        with app.app_context():
            job = Job(agent_id="agent-test-001", investigation_id="INV-001", ir=VALID_IR)
            job.transition_to(JobStatus.ASSIGNED)
            job.transition_to(JobStatus.RUNNING)
            job.transition_to(JobStatus.COMPLETED)
            assert job.status == JobStatus.COMPLETED
            assert job.completed_at is not None

    def test_running_to_failed(self, app):
        """RUNNING → FAILED is valid."""
        with app.app_context():
            job = Job(agent_id="agent-test-001", investigation_id="INV-001", ir=VALID_IR)
            job.transition_to(JobStatus.ASSIGNED)
            job.transition_to(JobStatus.RUNNING)
            job.transition_to(JobStatus.FAILED, error="timeout")
            assert job.status == JobStatus.FAILED
            assert job.error == "timeout"

    def test_queued_to_cancelled(self, app):
        """QUEUED → CANCELLED is valid."""
        with app.app_context():
            job = Job(agent_id="agent-test-001", investigation_id="INV-001", ir=VALID_IR)
            job.transition_to(JobStatus.CANCELLED)
            assert job.status == JobStatus.CANCELLED

    def test_completed_to_running_rejected(self, app):
        """COMPLETED → RUNNING is invalid (terminal state)."""
        with app.app_context():
            job = Job(agent_id="agent-test-001", investigation_id="INV-001", ir=VALID_IR)
            job.transition_to(JobStatus.ASSIGNED)
            job.transition_to(JobStatus.RUNNING)
            job.transition_to(JobStatus.COMPLETED)
            with pytest.raises(JobTransitionError):
                job.transition_to(JobStatus.RUNNING)

    def test_running_to_queued_rejected(self, app):
        """RUNNING → QUEUED is invalid."""
        with app.app_context():
            job = Job(agent_id="agent-test-001", investigation_id="INV-001", ir=VALID_IR)
            job.transition_to(JobStatus.ASSIGNED)
            job.transition_to(JobStatus.RUNNING)
            with pytest.raises(JobTransitionError):
                job.transition_to(JobStatus.QUEUED)


# ── Job Cancellation ──────────────────────────────────────────────────────────

class TestJobCancellation:
    def test_cancel_queued_job(self, client, registered_agent, investigation, app):
        """QUEUED job can be cancelled."""
        with app.app_context():
            job = Job(agent_id="agent-test-001", investigation_id="INV-TEST-001", ir=VALID_IR)
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id

        with app.app_context():
            resp = client.post(f"/api/v1/jobs/{job_id}/cancel")
        assert resp.status_code == 200

    def test_cancel_completed_job_rejected(self, client, registered_agent, investigation, app):
        """Completed job cannot be cancelled."""
        with app.app_context():
            job = Job(agent_id="agent-test-001", investigation_id="INV-TEST-001", ir=VALID_IR)
            job.transition_to(JobStatus.ASSIGNED)
            job.transition_to(JobStatus.RUNNING)
            job.transition_to(JobStatus.COMPLETED)
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id

        with app.app_context():
            resp = client.post(f"/api/v1/jobs/{job_id}/cancel")
        assert resp.status_code == 409


# ── Result Upload ─────────────────────────────────────────────────────────────

class TestResultUpload:
    import hashlib as _hashlib
    import json as _json

    def _make_evidence_item(self, op_id="op-001", op_type="system.info", data=None):
        import hashlib, json
        if data is None:
            data = {"hostname": "test-host"}
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        sha = hashlib.sha256(canonical.encode()).hexdigest()
        return {
            "evidence_id": f"EVD-{op_id}",
            "operation_id": op_id,
            "operation_type": op_type,
            "data": data,
            "sha256": sha,
            "schema_version": "1.0",
        }

    def _create_running_job(self, app, agent_id="agent-test-001"):
        with app.app_context():
            job = Job(agent_id=agent_id, investigation_id="INV-TEST-001", ir=VALID_IR)
            job.transition_to(JobStatus.ASSIGNED)
            job.transition_to(JobStatus.RUNNING)
            db.session.add(job)
            db.session.commit()
            return job.job_id

    def test_valid_result_upload(self, client, registered_agent, investigation, app):
        """Valid result upload transitions job to COMPLETED."""
        job_id = self._create_running_job(app)
        evidence = self._make_evidence_item()
        with app.app_context():
            resp = client.post(
                f"/api/v1/jobs/{job_id}/results",
                json={
                    "agent_id": "agent-test-001",
                    "status": "completed",
                    "results": [{"operation_id": "op-001", "status": "success"}],
                    "evidence": [evidence],
                },
                headers={"Authorization": f"Bearer {registered_agent['token']}"},
            )
        assert resp.status_code == 200
        assert resp.get_json()["job_status"] == "COMPLETED"

    def test_wrong_agent_result_rejected(self, client, registered_agent2, investigation, app):
        """Agent B cannot submit results for Agent A's job."""
        job_id = self._create_running_job(app, agent_id="agent-test-001")
        with app.app_context():
            resp = client.post(
                f"/api/v1/jobs/{job_id}/results",
                json={
                    "agent_id": "agent-test-002",
                    "status": "completed",
                    "results": [],
                    "evidence": [],
                },
                headers={"Authorization": f"Bearer {registered_agent2['token']}"},
            )
        assert resp.status_code == 403

    def test_result_upload_no_auth_rejected(self, client, registered_agent, investigation, app):
        """Result upload without token returns 401."""
        job_id = self._create_running_job(app)
        with app.app_context():
            resp = client.post(
                f"/api/v1/jobs/{job_id}/results",
                json={"agent_id": "agent-test-001", "status": "completed", "results": [], "evidence": []},
            )
        assert resp.status_code == 401

    def test_tampered_evidence_hash_rejected(self, client, registered_agent, investigation, app):
        """Tampered evidence SHA-256 is rejected."""
        job_id = self._create_running_job(app)
        evidence = self._make_evidence_item()
        evidence["sha256"] = "a" * 64  # wrong hash
        with app.app_context():
            resp = client.post(
                f"/api/v1/jobs/{job_id}/results",
                json={
                    "agent_id": "agent-test-001",
                    "status": "completed",
                    "results": [],
                    "evidence": [evidence],
                },
                headers={"Authorization": f"Bearer {registered_agent['token']}"},
            )
        assert resp.status_code == 400
        assert "integrity" in resp.get_json().get("error", "").lower()

    def test_result_upload_job_not_running_rejected(self, client, registered_agent, investigation, app):
        """Uploading results for an ASSIGNED (not RUNNING) job is rejected."""
        with app.app_context():
            job = Job(agent_id="agent-test-001", investigation_id="INV-TEST-001", ir=VALID_IR)
            job.transition_to(JobStatus.ASSIGNED)
            db.session.add(job)
            db.session.commit()
            job_id = job.job_id

        with app.app_context():
            resp = client.post(
                f"/api/v1/jobs/{job_id}/results",
                json={
                    "agent_id": "agent-test-001",
                    "status": "completed",
                    "results": [],
                    "evidence": [],
                },
                headers={"Authorization": f"Bearer {registered_agent['token']}"},
            )
        assert resp.status_code == 409


# ── Investigation Routes ──────────────────────────────────────────────────────

class TestInvestigationRoutes:
    def test_create_investigation(self, client, app):
        """Creating an investigation returns 201 with investigation_id."""
        with app.app_context():
            resp = client.post("/api/v1/investigations", json={"name": "Test Inv"})
        assert resp.status_code == 201
        data = resp.get_json()
        assert "investigation_id" in data
        assert data["name"] == "Test Inv"

    def test_list_investigations(self, client, investigation, app):
        """Listing investigations returns a list."""
        with app.app_context():
            resp = client.get("/api/v1/investigations")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_get_investigation(self, client, investigation, app):
        """Getting a specific investigation returns correct data."""
        with app.app_context():
            resp = client.get("/api/v1/investigations/INV-TEST-001")
        assert resp.status_code == 200
        assert resp.get_json()["investigation_id"] == "INV-TEST-001"

    def test_get_unknown_investigation_404(self, client, app):
        """Unknown investigation returns 404."""
        with app.app_context():
            resp = client.get("/api/v1/investigations/ghost-inv")
        assert resp.status_code == 404
