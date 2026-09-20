# Proteus Security Architecture

## Security Principles

PROTEUS is a **defensive** digital-forensics platform. Every design decision prioritizes security and auditability.

## What PROTEUS Will Never Do

| Prohibited | Reason |
|---|---|
| Execute arbitrary shell commands | `shell=True` is never used |
| Run arbitrary Python/PowerShell | No `eval()` or `exec()` |
| Accept raw source code as a job | IR schema validation enforces this |
| Send executable payloads to agents | Server only sends JOCKY IR |
| Allow one agent to access another's data | Per-agent token + ownership checks |
| Persist executable code | Jobs store only validated IR JSON |

## Authentication

Agents authenticate with Bearer tokens:

```
Authorization: Bearer <agent_token>
```

- Tokens are generated server-side at registration
- Tokens are returned **once** at registration — the agent must store them
- The server stores the token for lookup

### Protected Endpoints

| Endpoint | Auth Required |
|---|---|
| `GET /api/v1/agents/{id}/jobs/next` | ✅ Agent token |
| `POST /api/v1/jobs/{id}/ack` | ✅ Agent token |
| `POST /api/v1/jobs/{id}/results` | ✅ Agent token |
| `POST /api/v1/agent/register` | ❌ None (registration is open) |
| `POST /api/v1/agent/heartbeat` | ❌ Agent ID validated in body |
| `GET /api/v1/jobs` | ❌ Admin/internal |

## Authorization Rules

An agent **can**:
- Register
- Send heartbeats
- Poll its **own** jobs
- Acknowledge its **own** jobs
- Upload results for its **own** jobs

An agent **cannot**:
- Access another agent's jobs
- Create investigations
- Cancel jobs
- Modify the approved operation list
- Upload results for another agent's job

## Dual IR Validation

IR is validated **twice**:

```
JOCKY source
    ↓ (compiler)
IR JSON
    ↓
Server-side IR validation    ← First validation
    ↓
Job stored in DB
    ↓
Agent receives IR
    ↓
Agent-side IR validation     ← Second validation (defense in depth)
    ↓
OperationDispatcher (allowlist enforced)
    ↓
Forensic collector
```

Both validators enforce:
- Approved version
- Non-empty investigation name
- Non-empty operations list
- Unique operation IDs
- Approved operation types (10 allowed)
- No forbidden fields (`code`, `shell`, `exec`, `eval`, `script`, etc.)

## Evidence Integrity

SHA-256 is computed on the agent over canonical JSON of each evidence item. The server re-computes and verifies the hash before accepting results. This ensures:
- Evidence was not tampered with in transit
- Evidence matches what the agent actually collected
- Results are cryptographically auditable

## Audit Logging

All security-relevant events are logged by `manager/audit_logger.py`:

- `AGENT_REGISTERED` — new agent joined
- `JOB_CREATED` — investigation job dispatched
- `JOB_STARTED` — agent acknowledged job
- `JOB_COMPLETED` — forensic results accepted
- `JOB_FAILED` — agent reported failure
- `JOB_CANCELLED` — job cancelled
- `INVALID_IR_REJECTED` — malformed/unauthorized IR blocked
- `UNAUTHORIZED_REQUEST` — access control violation

Logs **never** contain: tokens, passwords, private keys, or credentials.
