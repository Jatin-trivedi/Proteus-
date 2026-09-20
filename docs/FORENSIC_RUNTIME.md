# Proteus JOCKY Forensic Runtime Architecture (Priority 4)

The Proteus Forensic Runtime executes validated JOCKY Intermediate Representation (Forensic IR) operations through strict, allowlisted read-only collectors. The agent never executes arbitrary shell commands or dynamic code based on operation names.

---

## 1. End-to-End Pipeline

```
JOCKY Source (.jocky)
         ↓
   Lexer & Parser
         ↓
 Abstract Syntax Tree (AST)
         ↓
  Semantic Validation
         ↓
     IR Generator
         ↓
 Forensic IR Document (JSON)
         ↓
    IR Validation
         ↓
  Operation Dispatcher
         ↓
Allowlisted Forensic Collectors
         ↓
    Structured Results
         ↓
   Investigation Result
```

---

## 2. Operation Mapping & Collector Specification

| JOCKY Language Function | IR Operation Type | Collector Class | Input Parameters | Output Data Schema |
|---|---|---|---|---|
| `system.info()` | `system.info` | `SystemInfoCollector` | `{}` | `{"hostname": str, "os": str, "architecture": str, "kernel": str, "uptime": str, "username": str}` |
| `system.users()` | `system.users` | `SystemUsersCollector` | `{}` | `{"users": [{"name": str, "type": "local"}]}` |
| `processes.list()` | `processes.list` | `ProcessesListCollector` | `{}` | `{"processes": [{"pid": int, "name": str, "parent_pid": int, "username": str}]}` |
| `processes.details(pid)` | `processes.details` | `ProcessesDetailsCollector` | `{"pid": int}` | `{"pid": int, "name": str, "parent_pid": int, "start_time": str, "executable": str}` |
| `network.interfaces()` | `network.interfaces` | `NetworkInterfacesCollector` | `{}` | `{"interfaces": [{"name": str, "addresses": [str], "mac": str}]}` |
| `network.connections()` | `network.connections` | `NetworkConnectionsCollector` | `{}` | `{"connections": [{"protocol": str, "local": str, "remote": str, "state": str, "pid": int}]}` |
| `network.routes()` | `network.routes` | `NetworkRoutesCollector` | `{}` | `{"routes": [{"destination": str, "gateway": str, "interface": str, "metric": int}]}` |
| `network.dns()` | `network.dns` | `NetworkDnsCollector` | `{}` | `{"dns_servers": [str], "search_domains": [str], "configuration": dict}` |
| `filesystem.metadata(path)` | `filesystem.metadata` | `FilesystemMetadataCollector` | `{"path": str}` | `{"path": str, "size": int, "creation_time": str, "modification_time": str, "access_time": str, "permissions": str}` |
| `filesystem.hash(path)` | `filesystem.hash` | `FilesystemHashCollector` | `{"path": str}` | `{"path": str, "algorithm": "SHA-256", "hash": str}` |

---

## 3. Standard Result & Error Format

### Successful Operation
```json
{
  "operation_id": "op-001",
  "type": "system.info",
  "status": "success",
  "data": {
    "hostname": "sec-node-1",
    "os": "Darwin",
    "architecture": "arm64",
    "kernel": "25.5.0",
    "uptime": "834190s",
    "username": "investigator"
  },
  "error": null
}
```

### Failed Operation (Error Isolated)
```json
{
  "operation_id": "op-009",
  "type": "filesystem.hash",
  "status": "error",
  "data": null,
  "error": {
    "code": "COLLECTION_FAILED",
    "message": "Path not found: './missing_evidence.dat'"
  }
}
```

### Standard Error Codes
- `UNKNOWN_OPERATION`: Operation is not in the approved forensic allowlist.
- `NOT_IMPLEMENTED`: Operation is recognized but lacks a registered collector implementation.
- `INVALID_PARAMETERS`: Missing, wrong type, or malformed parameters.
- `PERMISSION_DENIED`: Target resource access denied by operating system permissions.
- `COLLECTION_FAILED`: Non-fatal collector error (e.g. process not found, missing path, OS command failure).

---

## 4. Failure Isolation & Security Boundary

1. **Strict Allowlisting**: The runtime checks every operation against `APPROVED_OPERATIONS`. Any unauthorized operation type (e.g., `evil.operation`) is rejected immediately.
2. **Zero Arbitrary Execution**: The runtime does not evaluate arbitrary strings, spawn arbitrary shell commands, or perform dynamic reflection based on operation names.
3. **Resilient Sequential Execution**: If an individual collector encounters an error (e.g., non-existent PID, missing file, permission denial), the failure is isolated to that specific `OperationResult`. The `OperationDispatcher` continues executing all subsequent operations in the investigation without halting or crashing.
4. **Read-Only Forensics**: All collectors operate strictly in read-only mode, without file modification, process manipulation, memory modification, persistence, or bypass mechanisms.
