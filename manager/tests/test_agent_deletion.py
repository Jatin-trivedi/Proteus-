import os
import sys
import types

import pytest

MANAGER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if MANAGER_DIR not in sys.path:
    sys.path.insert(0, MANAGER_DIR)

from config import Config

_original_database_uri = Config.SQLALCHEMY_DATABASE_URI
_original_engine_options = Config.SQLALCHEMY_ENGINE_OPTIONS
Config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
Config.SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

if sys.platform == "win32" and "fcntl" not in sys.modules:
    fcntl = types.ModuleType("fcntl")
    fcntl.LOCK_EX = 1
    fcntl.LOCK_UN = 2
    fcntl.flock = lambda *_args: None
    sys.modules["fcntl"] = fcntl

from app import create_app
from models import Agent, Deploy, Evidence, Finding, Job, Result, Script, db


Config.SQLALCHEMY_DATABASE_URI = _original_database_uri
Config.SQLALCHEMY_ENGINE_OPTIONS = _original_engine_options


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setattr(Config, "SQLALCHEMY_ENGINE_OPTIONS", {"pool_pre_ping": True})
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_delete_offline_agent_and_related_records(app):
    agent_id = "offline-agent-delete-test"
    with app.app_context():
        agent = Agent(
            agent_id=agent_id,
            hostname="offline-host",
            os="linux",
            status="offline",
        )
        script = Script(script_id="script-delete-test", name="test-script", code="pass")
        result = Result(
            result_id="result-delete-test",
            agent_id=agent_id,
            script_id=script.script_id,
            data_encrypted="encrypted",
        )
        job = Job(
            job_id="job-delete-test",
            agent_id=agent_id,
            investigation_id="INV-delete-test",
            ir={},
        )
        deploy = Deploy(
            deploy_id="deploy-delete-test",
            agent_id=agent_id,
            script_id=script.script_id,
            result_id=result.result_id,
        )
        finding = Finding(
            finding_id="finding-delete-test",
            result_id=result.result_id,
            agent_id=agent_id,
            category="test",
            title="Test finding",
            description="Test",
        )
        evidence = Evidence(
            evidence_id="evidence-delete-test",
            job_id=job.job_id,
            agent_id=agent_id,
            operation_id="OP-delete-test",
            operation_type="test",
            data={},
            sha256="0" * 64,
        )
        db.session.add_all([agent, script, result, job])
        db.session.flush()
        db.session.add_all([deploy, finding, evidence])
        db.session.commit()

    response = app.test_client().delete(f"/api/v1/agent/{agent_id}")

    assert response.status_code == 200
    assert response.get_json() == {"status": "deleted", "agent_id": agent_id}
    with app.app_context():
        assert db.session.get(Agent, agent_id) is None
        assert db.session.get(Deploy, "deploy-delete-test") is None
        assert db.session.get(Result, "result-delete-test") is None
        assert db.session.get(Finding, "finding-delete-test") is None
        assert db.session.get(Evidence, "evidence-delete-test") is None
        assert db.session.get(Job, "job-delete-test") is None
        assert db.session.get(Script, "script-delete-test") is not None
