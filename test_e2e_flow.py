"""End-to-end smoke test for manager -> relay -> agent -> manager."""

import json
import os
import sys
import threading
import time
from urllib.request import Request, urlopen

import pytest
from flask import Flask, Response, request
from werkzeug.serving import make_server

ROOT = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(ROOT, "manager"))
sys.path.insert(0, ROOT)

from config import Config


def _json_request(url, method="GET", payload=None, token=None):
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, data=data, headers=headers, method=method), timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_agent_relay_manager_job_flow(tmp_path):
    """Start both local HTTP hops and verify heartbeat, dispatch, and results."""
    db_path = tmp_path / "smoke.db"
    Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    Config.DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI

    from app import create_app
    from models import Agent, Job, db
    from runtime.agent.config import AgentConfig
    from runtime.agent.polling import AgentPollingLoop

    manager_app = create_app()
    manager_server = make_server("127.0.0.1", 0, manager_app)
    manager_thread = threading.Thread(target=manager_server.serve_forever, daemon=True)
    manager_thread.start()
    manager_url = f"http://127.0.0.1:{manager_server.server_port}"

    relay_app = Flask("local-relay")

    @relay_app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    @relay_app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    def relay(path):
        body = request.get_data() or None
        headers = {
            key: value for key, value in request.headers.items()
            if key.lower() in {"accept", "authorization", "content-type"}
        }
        try:
            with urlopen(
                Request(f"{manager_url}/{path}", data=body, headers=headers, method=request.method),
                timeout=5,
            ) as response:
                return Response(response.read(), status=response.status, content_type="application/json")
        except Exception as error:
            return {"error": str(error)}, 502

    relay_server = make_server("127.0.0.1", 0, relay_app)
    relay_thread = threading.Thread(target=relay_server.serve_forever, daemon=True)
    relay_thread.start()
    relay_url = f"http://127.0.0.1:{relay_server.server_port}"

    loop = None
    try:
        config = AgentConfig()
        config.server_url = relay_url
        config.poll_interval = 1
        config.http_timeout = 5
        config.job_timeout = 30
        config.hostname = "e2e-smoke-agent"
        config.os_type = "linux"
        config.architecture = "x86_64"
        loop = AgentPollingLoop(config)
        agent_thread = loop.start_background()

        deadline = time.time() + 10
        agent_id = None
        while time.time() < deadline:
            with manager_app.app_context():
                agent = Agent.query.filter_by(hostname="e2e-smoke-agent").first()
                if agent:
                    agent_id = agent.agent_id
                    assert agent.status == "ONLINE"
                    break
            time.sleep(0.1)
        assert agent_id, "agent registration/heartbeat did not reach manager DB"
        assert loop.agent_token

        status, created = _json_request(
            f"{relay_url}/api/v1/jobs",
            method="POST",
            payload={
                "agent_id": agent_id,
                "investigation_id": "INV-E2E",
                "ir": {
                    "version": "1.0",
                    "ir_type": "jocky_forensic_ir",
                    "investigation": "E2E smoke",
                    "operations": [{"id": "op-001", "type": "system.info", "parameters": {}}],
                },
            },
        )
        assert status == 201
        job_id = created["job_id"]

        deadline = time.time() + 20
        while time.time() < deadline:
            with manager_app.app_context():
                job = db.session.get(Job, job_id)
                if job and job.status == "COMPLETED":
                    break
            time.sleep(0.2)
        else:
            pytest.fail("agent did not complete the dispatched job")

        status, result = _json_request(f"{relay_url}/api/v1/jobs/{job_id}")
        assert status == 200
        assert result["status"] == "COMPLETED"
        assert result["evidence"]
    finally:
        if loop:
            loop.stop()
        relay_server.shutdown()
        manager_server.shutdown()
