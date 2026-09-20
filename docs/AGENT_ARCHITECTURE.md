# Proteus Agent Architecture

## Overview

PROTEUS is a defensive digital-forensics framework. Forensic agents are distributed nodes that run on target systems, receive validated JOCKY IR jobs from the central manager, execute approved forensic operations, and upload structured evidence with cryptographic integrity.

```mermaid
graph TD
    UI["PROTEUS UI\nInvestigation Control"]
    API["PROTEUS Manager API\nAgent Mgmt · Job Mgmt · Investigation Mgmt"]
    A1["Agent 1\nWindows"]
    A2["Agent 2\nLinux"]
    A3["Agent 3\nWindows"]

    UI --> API
    API --> A1
    API --> A2
    API --> A3

    A1 --> V1["Validate IR\n(Agent-Side)"]
    A2 --> V2["Validate IR\n(Agent-Side)"]
    A3 --> V3["Validate IR\n(Agent-Side)"]

    V1 --> D1["Dispatcher\n10 Forensic Ops"]
    V2 --> D2["Dispatcher\n10 Forensic Ops"]
    V3 --> D3["Dispatcher\n10 Forensic Ops"]

    D1 --> E["Evidence + SHA-256"]
    D2 --> E
    D3 --> E

    E --> API
```

## Agent Lifecycle

```mermaid
sequenceDiagram
    participant Agent
    participant Manager

    Agent->>Manager: POST /api/v1/agent/register
    Manager-->>Agent: {agent_id, agent_token, heartbeat_interval}

    loop Every heartbeat_interval
        Agent->>Manager: POST /api/v1/agent/heartbeat {agent_id, status}
        Manager-->>Agent: {status: ok}
    end

    loop Every poll_interval
        Agent->>Manager: GET /api/v1/agents/{agent_id}/jobs/next
        Manager-->>Agent: {job: {job_id, ir, ...}} or {job: null}

        opt Job available
            Agent->>Manager: POST /api/v1/jobs/{job_id}/ack {agent_id}
            Note over Agent: Validate IR (agent-side)
            Note over Agent: Execute forensic operations
            Note over Agent: Generate evidence + SHA-256
            Agent->>Manager: POST /api/v1/jobs/{job_id}/results {evidence}
            Manager-->>Agent: {status: accepted}
        end
    end
```

## Agent Package Structure

```
runtime/agent/
├── __init__.py         — package exports
├── contracts.py        — typed request/response models (Priority 6)
├── heartbeat_client.py — background heartbeat worker
├── ir_validator.py     — agent-side IR validation (Priority 8)
├── evidence.py         — EvidenceItem + SHA-256 integrity
├── job_executor.py     — orchestrates full job pipeline
├── config.py           — environment-based configuration
├── polling.py          — main polling loop
└── main.py             — entry point (python -m runtime.agent)
```

## Security Boundary

The agent **only** executes operations in the approved allowlist:

| Operation | Description |
|---|---|
| `system.info` | OS, hostname, uptime |
| `system.users` | Local user accounts |
| `processes.list` | Running processes |
| `processes.details` | Process detail by PID |
| `network.interfaces` | Network adapter info |
| `network.connections` | Active TCP/UDP connections |
| `network.routes` | Routing table |
| `network.dns` | DNS configuration |
| `filesystem.metadata` | File metadata |
| `filesystem.hash` | File SHA-256 hash |

The agent **never**:
- Executes arbitrary Python, shell, or PowerShell
- Uses `eval()`, `exec()`, `shell=True`
- Accepts raw source code as a job
- Modifies evidence after collection

## Running the Agent

```bash
# Set configuration
export PROTEUS_SERVER_URL=http://localhost:5000
export LOG_LEVEL=INFO

# Run agent
.venv/bin/python -m runtime.agent

# Or with all options
PROTEUS_SERVER_URL=http://localhost:5000 \
HEARTBEAT_INTERVAL=30 \
POLL_INTERVAL=15 \
JOB_TIMEOUT=300 \
.venv/bin/python -m runtime.agent
```
