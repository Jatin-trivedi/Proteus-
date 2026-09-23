#!/usr/bin/env python3
"""Verify the CI build and IR execution integration without a live agent."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


repo_root = Path(__file__).resolve().parent
results: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str = "") -> None:
    tag = "PASS" if passed else "FAIL"
    print(f"[{tag}] {name}")
    if detail:
        print(f"       {detail}")
    results.append((name, passed, detail))


def verify_step_1() -> None:
    print("\nSTEP 1 - ci_build.py")
    ci_script = repo_root / "ci_build.py"
    check("ci_build.py exists", ci_script.exists())
    if not ci_script.exists():
        return

    source = ci_script.read_text()
    check("Uses secrets.token_hex", "secrets.token_hex" in source)
    check("Injects main.C2_AUTH", "-X main.C2_AUTH" in source)
    check("Injects main.xorKeyHex", "-X main.xorKeyHex" in source)
    check("Reports SHA-256", "sha256" in source.lower())

    build_dir = Path(tempfile.mkdtemp(prefix="proteus-build-", dir=repo_root))
    try:
        hashes: list[str] = []
        for run_number in (1, 2):
            result = subprocess.run(
                [
                    sys.executable,
                    str(ci_script),
                    "--output-dir",
                    str(build_dir),
                    "--os",
                    "windows",
                    "--arch",
                    "amd64",
                ],
                capture_output=True,
                text=True,
                cwd=repo_root,
            )
            if result.returncode != 0:
                check(
                    f"Build run {run_number} succeeds",
                    False,
                    result.stderr[-500:] or result.stdout[-500:],
                )
                return

            binaries = list(build_dir.glob("agent_*.exe"))
            if not binaries:
                check(f"Build run {run_number} produces an executable", False)
                return

            binary = max(binaries, key=lambda path: path.stat().st_mtime_ns)
            digest = hashlib.sha256(binary.read_bytes()).hexdigest()
            hashes.append(digest)
            check(f"Build run {run_number} succeeds", True, digest)

        check(
            "Two builds produce different SHA-256 hashes",
            hashes[0] != hashes[1],
            "polymorphic values changed the binary" if hashes[0] != hashes[1] else "hashes are identical",
        )
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)


def verify_step_2() -> None:
    print("\nSTEP 2 - IR integration")
    main_go = repo_root / "agent" / "main.go"
    ir_executor = repo_root / "agent" / "ir_executor.go"
    routes = repo_root / "manager" / "api" / "script_routes.py"

    check("agent/main.go exists", main_go.exists())
    check("agent/ir_executor.go exists", ir_executor.exists())
    check("script_routes.py exists", routes.exists())
    if main_go.exists():
        source = main_go.read_text()
        kill_switch = source.find('case "__exit__"')
        ir_dispatch = source.find('strings.HasPrefix(script, "{")')
        check("IR JSON dispatch is present", ir_dispatch >= 0)
        check("IR executor is called", "executeIRDocumentJSON(script)" in source)
        check("Kill switch precedes IR dispatch", 0 <= kill_switch < ir_dispatch)
        check("IR result is marshalled", "json.Marshal(result)" in source)
    if ir_executor.exists():
        source = ir_executor.read_text()
        for operation in (
            "system.info",
            "processes.list",
            "network.connections",
            "network.interfaces",
            "filesystem.hash",
        ):
            check(f"IR executor handles {operation}", f'"{operation}"' in source)

    if routes.exists():
        sys.path.insert(0, str(repo_root / "manager"))
        try:
            from api.script_routes import _compile_jocky_to_ir
        except ImportError as error:
            check("Manager compiler helper imports", False, str(error))
            return

        valid_source = textwrap.dedent(
            '''\
            analysis "Verify Test" {
                system.info();
                processes.list();
                network.connections();
            }
            '''
        )
        ir_json, error = _compile_jocky_to_ir(valid_source)
        check("Valid JOCKY compiles to IR JSON", ir_json is not None and error is None, error or "")
        if ir_json is not None:
            try:
                document = json.loads(ir_json)
                check("IR output is valid JSON", True)
                check("IR type is correct", document.get("ir_type") == "jocky_forensic_ir")
                operations = document.get("operations", [])
                check("IR operations are non-empty", bool(operations))
                check("IR operations have id and type", all("id" in op and "type" in op for op in operations))
            except json.JSONDecodeError as error:
                check("IR output is valid JSON", False, str(error))

        invalid_json, invalid_error = _compile_jocky_to_ir("not valid jocky @@###")
        check("Invalid JOCKY returns an error", invalid_json is None and isinstance(invalid_error, str))


def main() -> int:
    verify_step_1()
    verify_step_2()
    passed = sum(passed for _, passed, _ in results)
    print(f"\n{passed}/{len(results)} checks passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
