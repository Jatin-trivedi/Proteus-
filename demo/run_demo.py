#!/usr/bin/env python3
"""
Proteus End-to-End Demo (Priority 13)

Demonstrates the full forensic agent pipeline:
  1. Start PROTEUS API
  2. Register agent → receive agent_id + token
  3. Send heartbeat
  4. Create investigation
  5. Compile JOCKY source → IR
  6. Create job with validated IR
  7. Agent polls → receives job
  8. Agent validates IR (agent-side)
  9. Agent executes approved operations
  10. Evidence generated + SHA-256 integrity
  11. Agent uploads results
  12. Server verifies result
  13. Query investigation results

Usage:
    # In terminal 1, start the manager API:
    cd manager && ../.venv/bin/python app.py

    # In terminal 2, run the demo:
    PROTEUS_SERVER_URL=http://localhost:5000 ../.venv/bin/python demo/run_demo.py

    # Or run everything in one script (starts embedded test server):
    ../.venv/bin/python demo/run_demo.py --embedded
"""

import argparse
import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request

# Ensure project root is on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANAGER_DIR = os.path.join(ROOT, "manager")
sys.path.insert(0, ROOT)
sys.path.insert(0, MANAGER_DIR)

SERVER_URL = os.getenv("PROTEUS_SERVER_URL", "http://localhost:5000")


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def http(method, path, payload=None, token=None, timeout=10):
    url = f"{SERVER_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode()
            return json.loads(body) if body else {}, r.status
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return json.loads(body), e.code
        except Exception:
            return {"error": body}, e.code


def section(title):
    print(f"\n{'═' * 60}")
    print(f"  {title}")
    print(f"{'═' * 60}")


def ok(msg, data=None):
    print(f"  ✅  {msg}")
    if data:
        print(f"      {json.dumps(data, indent=6)[:300]}")


def fail(msg, data=None):
    print(f"  ❌  {msg}")
    if data:
        print(f"      {json.dumps(data)[:300]}")
    sys.exit(1)


# ── Demo steps ────────────────────────────────────────────────────────────────

def demo_health():
    section("Step 0: Health Check")
    resp, code = http("GET", "/health")
    if code == 200:
        ok("API is healthy", resp)
    else:
        fail("API is not reachable — is the server running?", resp)


def demo_register():
    section("Step 1: Agent Registration")
    payload = {
        "hostname": "demo-host",
        "os": "linux",
        "architecture": "x86_64",
        "version": "1.0.0",
        "capabilities": [],
    }
    resp, code = http("POST", "/api/v1/agent/register", payload)
    if code != 200:
        fail("Registration failed", resp)
    agent_id = resp.get("agent_id")
    ok(f"Registered as {agent_id}", resp)
    return agent_id, resp.get("agent_token")


def demo_heartbeat(agent_id):
    section("Step 2: Heartbeat")
    resp, code = http("POST", "/api/v1/agent/heartbeat", {
        "agent_id": agent_id,
        "status": "online",
    })
    if code != 200:
        fail("Heartbeat failed", resp)
    ok("Heartbeat accepted", resp)


def demo_investigation():
    section("Step 3: Create Investigation")
    resp, code = http("POST", "/api/v1/investigations", {
        "name": "Demo Network Investigation",
        "description": "End-to-end forensic demo",
    })
    if code != 201:
        fail("Failed to create investigation", resp)
    inv_id = resp["investigation_id"]
    ok(f"Investigation created: {inv_id}")
    return inv_id


def demo_build_ir(investigation_id):
    """
    Build a JOCKY IR document.
    In production this would come from the JOCKY compiler.
    For the demo we construct it directly.
    """
    section("Step 4: Build JOCKY IR")
    ir = {
        "version": "1.0",
        "ir_type": "jocky_forensic_ir",
        "investigation": "Demo Network Investigation",
        "operations": [
            {"id": "op-001", "type": "system.info", "parameters": {}},
            {"id": "op-002", "type": "network.interfaces", "parameters": {}},
            {"id": "op-003", "type": "network.connections", "parameters": {}},
            {"id": "op-004", "type": "network.dns", "parameters": {}},
        ],
    }
    ok(f"IR built with {len(ir['operations'])} operations")
    return ir


def demo_create_job(agent_id, investigation_id, ir):
    section("Step 5: Create Job (server validates IR)")
    resp, code = http("POST", "/api/v1/jobs", {
        "agent_id": agent_id,
        "investigation_id": investigation_id,
        "ir": ir,
    })
    if code != 201:
        fail("Job creation failed", resp)
    job_id = resp["job_id"]
    ok(f"Job created: {job_id} (status: {resp['status']})")
    return job_id


def demo_poll_job(agent_id, agent_token, job_id):
    section("Step 6: Agent Polls for Job")
    resp, code = http("GET", f"/api/v1/agents/{agent_id}/jobs/next", token=agent_token)
    if code != 200:
        fail("Poll failed", resp)
    job = resp.get("job")
    if not job:
        fail("No job returned — expected job to be available")
    assert job["job_id"] == job_id, f"Got unexpected job {job['job_id']}"
    ok(f"Job polled: {job['job_id']}")
    return job


def demo_ack_job(agent_id, agent_token, job_id):
    section("Step 7: Agent Acknowledges Job (ASSIGNED → RUNNING)")
    resp, code = http("POST", f"/api/v1/jobs/{job_id}/ack",
                      {"agent_id": agent_id}, token=agent_token)
    if code != 200:
        fail("ACK failed", resp)
    ok("Job acknowledged → RUNNING")


def demo_execute_job(agent_id, job):
    section("Step 8-10: Agent Validates IR + Executes + Generates Evidence")
    job_id = job["job_id"]
    ir = job["ir"]
    investigation_id = job["investigation_id"]

    # Import executor (agent-side)
    from runtime.agent.job_executor import JobExecutor
    executor = JobExecutor(agent_id=agent_id, timeout_sec=60)
    result = executor.execute_job(job_id=job_id, investigation_id=investigation_id, ir=ir)

    if result["status"] == "failed":
        fail(f"Execution failed: {result.get('error')}")

    ok(f"Execution complete — {len(result['results'])} operations, {len(result['evidence'])} evidence items")

    for ev in result["evidence"]:
        op = ev["operation_type"]
        sha = ev["sha256"][:16]
        ok(f"  Evidence [{op}] sha256={sha}…")

    return result


def demo_upload_results(agent_id, agent_token, job_id, result):
    section("Step 11: Upload Results (server verifies integrity)")
    payload = {
        "agent_id": agent_id,
        "status": result["status"],
        "results": result["results"],
        "evidence": result["evidence"],
        "integrity": result["integrity"],
    }
    resp, code = http("POST", f"/api/v1/jobs/{job_id}/results", payload, token=agent_token)
    if code != 200:
        fail("Result upload failed", resp)
    ok(f"Results uploaded — job is now {resp['job_status']}")


def demo_query_results(investigation_id):
    section("Step 12: Query Investigation Results")
    resp, code = http("GET", f"/api/v1/investigations/{investigation_id}/results")
    if code != 200:
        fail("Failed to query investigation results", resp)
    jobs = resp.get("jobs", [])
    ok(f"Investigation has {len(jobs)} job(s)")
    for j in jobs:
        ev_count = len(j.get("evidence", []))
        ok(f"  Job {j['job_id']} — status={j['status']}, evidence={ev_count} items")
    return resp


def demo_get_job(job_id):
    section("Step 13: Get Final Job Status")
    resp, code = http("GET", f"/api/v1/jobs/{job_id}")
    if code != 200:
        fail("Failed to get job", resp)
    ok(f"Final job status: {resp['status']}")
    return resp


# ── Embedded server ───────────────────────────────────────────────────────────

def start_embedded_server():
    """Start the Flask manager API in a background thread."""
    import os
    os.environ.setdefault("DATABASE_URL", "")  # use SQLite

    from manager.app import create_app
    app = create_app()
    t = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False),
        daemon=True,
    )
    t.start()
    # Wait for server to start
    for _ in range(20):
        try:
            urllib.request.urlopen("http://127.0.0.1:5000/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Proteus E2E Demo")
    parser.add_argument("--embedded", action="store_true",
                        help="Start embedded Flask server (no separate process needed)")
    args = parser.parse_args()

    print("\n" + "█" * 60)
    print("  PROTEUS — End-to-End Forensic Demo")
    print("  Priority 6 / 7 / 8 — Agent + Job + Evidence")
    print("█" * 60)

    if args.embedded:
        print("\n  Starting embedded manager API…")
        if not start_embedded_server():
            fail("Embedded server failed to start")
        print("  ✅  Embedded server ready")

    demo_health()
    agent_id, agent_token = demo_register()
    demo_heartbeat(agent_id)
    inv_id = demo_investigation()
    ir = demo_build_ir(inv_id)
    job_id = demo_create_job(agent_id, inv_id, ir)
    job = demo_poll_job(agent_id, agent_token, job_id)
    demo_ack_job(agent_id, agent_token, job_id)
    result = demo_execute_job(agent_id, job)
    demo_upload_results(agent_id, agent_token, job_id, result)
    demo_query_results(inv_id)
    final = demo_get_job(job_id)

    section("Demo Complete")
    print(f"\n  ✅  Full forensic pipeline completed successfully!")
    print(f"  Agent:         {agent_id}")
    print(f"  Investigation: {inv_id}")
    print(f"  Job:           {job_id}")
    print(f"  Final status:  {final.get('status', '?')}")
    print()


if __name__ == "__main__":
    main()
