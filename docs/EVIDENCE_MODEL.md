# Proteus Evidence Model

## Evidence Item

Each forensic operation produces one `EvidenceItem`:

```json
{
  "evidence_id": "EVD-a1b2c3d4e5f6",
  "job_id": "JOB-abc123",
  "agent_id": "agent-xyz",
  "operation_id": "op-002",
  "operation_type": "network.connections",
  "collected_at": "2026-09-21T01:15:00+00:00",
  "data": { "connections": [...] },
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "schema_version": "1.0"
}
```

## SHA-256 Integrity Pipeline

```
Evidence Data (dict)
      ↓
json.dumps(sort_keys=True, separators=(',', ':'))
      ↓
Canonical JSON string
      ↓
.encode("utf-8")
      ↓
UTF-8 bytes
      ↓
hashlib.sha256(bytes).hexdigest()
      ↓
SHA-256 hex string (64 chars)
```

Key properties:
- **Deterministic**: same data → same hash, always
- **Canonical**: key order doesn't matter (sorted)
- **Compact**: no whitespace in JSON (cannot be reformatted to change hash)
- **Immutable**: hash is computed once at collection time; data must not be modified

## Evidence Package

A complete job result includes all evidence items plus a package-level integrity hash:

```json
{
  "schema_version": "1.0",
  "job_id": "JOB-abc123",
  "agent_id": "agent-xyz",
  "investigation_id": "INV-001",
  "started_at": "2026-09-21T01:14:00+00:00",
  "completed_at": "2026-09-21T01:15:00+00:00",
  "status": "completed",
  "operations": [...],
  "evidence": [...],
  "integrity": {
    "algorithm": "SHA-256",
    "package_hash": "..."
  }
}
```

The `package_hash` is computed over the canonical JSON of the `operations` list.

## Server-Side Verification

When the agent uploads results, the server:
1. Verifies the job exists and is `RUNNING`
2. Verifies the agent is the assigned agent
3. Recomputes each evidence item's SHA-256 and compares against the uploaded hash
4. Verifies the package-level integrity hash
5. Persists `Evidence` records to the database
6. Transitions job to `COMPLETED` or `FAILED`

## Querying Evidence

```
GET /api/v1/jobs/{job_id}
→ Returns job details including all evidence items

GET /api/v1/investigations/{investigation_id}/results
→ Returns all jobs and evidence for an investigation
```
