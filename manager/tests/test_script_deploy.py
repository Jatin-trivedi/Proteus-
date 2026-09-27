import json
import os
import sys
from unittest.mock import patch

import pytest
from flask import Flask

MANAGER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if MANAGER_DIR not in sys.path:
    sys.path.insert(0, MANAGER_DIR)

from api.script_routes import script_bp, _compile_legacy_jocky_if_needed
from models import db


@pytest.fixture
def client():
    test_app = Flask(__name__)
    test_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )
    db.init_app(test_app)
    test_app.register_blueprint(script_bp)
    return test_app.test_client()


def test_deploy_rejects_uncompilable_jocky_without_creating_deployment(client):
    with patch.object(db.session, "add") as add, patch.object(db.session, "commit") as commit:
        response = client.post(
            "/api/v1/script/deploy",
            json={
                "name": "invalid-script",
                "agent_ids": ["agent-test-001"],
                "code": 'agent invalid { run("whoami"); }',
            },
        )

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "JOCKY compilation failed"
    assert "at least one supported forensic operation" in body["details"]
    add.assert_not_called()
    commit.assert_not_called()


def test_legacy_jocky_is_compiled_to_ir_before_agent_delivery():
    code = '''analysis "Jocky Main" {
    system.info();
    system.users();
}'''

    compiled, error = _compile_legacy_jocky_if_needed(code)

    assert error is None
    ir = json.loads(compiled)
    assert [operation["type"] for operation in ir["operations"]] == [
        "system.info",
        "system.users",
    ]


def test_legacy_jocky_with_calls_outside_analysis_block_is_rejected():
    code = '''analysis "Jocky Main" {
}
system.info();
system.users();'''

    compiled, error = _compile_legacy_jocky_if_needed(code)

    assert compiled is None
    assert error is not None
    assert "unexpected token 'system'" in error
