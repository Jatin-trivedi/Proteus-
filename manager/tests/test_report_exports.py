import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from audit_logger import log_event
from models import db, Agent, Finding, Result, Script


@pytest.fixture
def app(tmp_path):
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["AUDIT_LOG_PATH"] = str(tmp_path / "audit.log")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def seed_report_data(app, suffix):
    agent_id = f"agent-siem-{suffix}"
    script_id = f"script-siem-{suffix}"
    result_id = f"result-siem-{suffix}"
    finding_id = f"finding-siem-{suffix}"
    with app.app_context():
        agent = Agent(
            agent_id=agent_id,
            hostname="siem-host",
            os="linux",
            architecture="x86_64",
        )
        script = Script(script_id=script_id, name="inventory", code="system.info")
        result = Result(
            result_id=result_id,
            agent_id=agent.agent_id,
            script_id=script.script_id,
            data_encrypted="encrypted-result",
        )
        finding = Finding(
            finding_id=finding_id,
            result_id=result.result_id,
            agent_id=agent.agent_id,
            severity="high",
            category="integrity",
            title="Evidence changed",
            description="The evidence digest does not match.",
        )
        db.session.add_all([agent, script, result, finding])
        db.session.commit()
        log_event(
            "EVIDENCE_STORED",
            agent_id=agent.agent_id,
            detail="Evidence stored",
            extra={"token": "must-not-export", "artifact_count": 1},
        )


def test_siem_export_contains_findings_and_redacted_audit_events(client, app):
    seed_report_data(app, "001")

    response = client.get(
        "/api/v1/report/export/siem",
        query_string={"agent_id": "agent-siem-001"},
    )

    assert response.status_code == 200
    assert response.mimetype == "application/ld+json"
    assert "attachment" in response.headers["Content-Disposition"]

    document = json.loads(response.get_data(as_text=True))
    assert document["@type"] == "SecurityEventBundle"
    assert document["event_count"] == 2
    assert {event["event_type"] for event in document["events"]} == {"finding", "audit"}
    assert all("must-not-export" not in json.dumps(event) for event in document["events"])


def test_siem_export_applies_finding_and_audit_filters(client, app):
    seed_report_data(app, "002")

    response = client.get(
        "/api/v1/report/export/siem",
        query_string={"agent_id": "agent-siem-002", "event_type": "EVIDENCE_STORED"},
    )

    document = json.loads(response.get_data(as_text=True))
    assert document["filters"] == {
        "agent_id": "agent-siem-002",
        "event_type": "EVIDENCE_STORED",
    }
    assert document["event_count"] == 2
    assert all(
        event["event_type"] in {"finding", "audit"}
        for event in document["events"]
    )
