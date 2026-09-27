import json
import os
import subprocess
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


def test_compiler_imports_with_manager_as_the_deployment_root():
    source = '''analysis "Vercel Bundle Test" {
    system.info();
}'''
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    command = (
        "import json; "
        "from compiler.compiler import Compiler; "
        f"result = Compiler().compile({source!r}); "
        "assert result.success, result.format_diagnostics(); "
        "print(json.dumps(result.ir))"
    )

    result = subprocess.run(
        [sys.executable, "-c", command],
        cwd=MANAGER_DIR,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    ir = json.loads(result.stdout)
    assert ir["operations"][0]["type"] == "system.info"


def test_bundled_compiler_core_matches_the_source_package():
    repo_compiler_dir = os.path.join(MANAGER_DIR, "..", "compiler")
    bundled_compiler_dir = os.path.join(MANAGER_DIR, "compiler")
    files = (
        "__init__.py",
        "compiler.py",
        "diagnostics/__init__.py",
        "diagnostics/diagnostics.py",
        "lexer/__init__.py",
        "lexer/tokenizer.py",
        "lexer/tokens.py",
        "parser/__init__.py",
        "parser/ast.py",
        "parser/parser.py",
        "semantic/__init__.py",
        "semantic/analyzer.py",
        "semantic/registry.py",
        "ir/__init__.py",
        "ir/generator.py",
        "ir/model.py",
        "ir/validator.py",
    )

    for relative_path in files:
        with open(os.path.join(repo_compiler_dir, relative_path), "rb") as source_file:
            source = source_file.read()
        with open(os.path.join(bundled_compiler_dir, relative_path), "rb") as bundled_file:
            bundled = bundled_file.read()
        assert bundled == source, f"Bundled compiler file is stale: {relative_path}"
