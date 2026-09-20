# JOCKY Forensic Intermediate Representation (IR)

## 1. Why JOCKY IR Exists
The **JOCKY Forensic IR** is a decoupled, deterministic JSON intermediate representation that bridges the gap between high-level forensic analysis scripts and low-level agent execution engines.

### Key Benefits
- **Decoupled Execution**: Isolates language parsing/syntax from target operating system implementations.
- **Safety Assurance**: Guarantees that only semantically verified, approved forensic collectors can ever be dispatched to endpoints.
- **Cross-Platform Portability**: Windows and Ubuntu endpoint agents execute the same structured IR payload using their respective platform collectors.
- **Auditability & Determinism**: Every IR artifact is reproducible, versioned, and machine-verifiable.

---

## 2. Top-Level IR Schema

```json
{
  "version": "1.0",
  "type": "forensic_analysis",
  "name": "<Analysis Name>",
  "operations": [
    {
      "id": 1,
      "namespace": "<namespace>",
      "function": "<function>",
      "arguments": [],
      "category": "<category>"
    }
  ]
}
```

---

## 3. Operation Specification & Categories

Each operation in `operations` contains:
- `id` (*integer*): Deterministic 1-based sequential operation counter preserving source order.
- `namespace` (*string*): Collector namespace (`system`, `processes`, `network`, `filesystem`).
- `function` (*string*): Specific collector function (e.g. `info`, `list`, `details`, `connections`, `hash`).
- `arguments` (*array*): Ordered argument literals.
- `category` (*string*): Domain category (`system`, `process`, `network`, `filesystem`).

### Registry of Approved Operations & Categories

| Namespace | Function | Arguments | Category | Description |
|---|---|---|---|---|
| `system` | `info()` | `[]` | `system` | Host OS, hostname, kernel, architecture, uptime |
| `system` | `users()` | `[]` | `system` | Local user accounts, active sessions, privilege levels |
| `processes` | `list()` | `[]` | `process` | Process table (PID, PPID, executable path, memory) |
| `processes` | `details(pid)` | `[pid: number]` | `process` | Process deep-dive (threads, handles, loaded DLLs, env) |
| `network` | `interfaces()` | `[]` | `network` | Network adapters, MAC addresses, IP addresses |
| `network` | `connections()` | `[]` | `network` | Active TCP/UDP sockets and listening ports |
| `network` | `routes()` | `[]` | `network` | Kernel routing table and gateway routes |
| `network` | `dns()` | `[]` | `network` | DNS cache entries and resolver configuration |
| `filesystem` | `metadata(path)` | `[path: string]` | `filesystem` | File MACB timestamps, permissions, size, attributes |
| `filesystem` | `hash(path)` | `[path: string]` | `filesystem` | Cryptographic hashes (SHA-256, MD5) of target path |

---

## 4. Complete Example

### Source (`examples/complete_investigation.jocky`)
```jocky
analysis "Complete System Investigation" {
    system.info();
    system.users();
    processes.list();
    network.interfaces();
    network.connections();
    network.routes();
    network.dns();
    filesystem.metadata("./evidence");
    filesystem.hash("./evidence");
}
```

### Generated IR (`build/complete_investigation.ir.json`)
```json
{
  "version": "1.0",
  "type": "forensic_analysis",
  "name": "Complete System Investigation",
  "operations": [
    {
      "id": 1,
      "namespace": "system",
      "function": "info",
      "arguments": [],
      "category": "system"
    },
    {
      "id": 2,
      "namespace": "system",
      "function": "users",
      "arguments": [],
      "category": "system"
    },
    {
      "id": 3,
      "namespace": "processes",
      "function": "list",
      "arguments": [],
      "category": "process"
    },
    {
      "id": 4,
      "namespace": "network",
      "function": "interfaces",
      "arguments": [],
      "category": "network"
    },
    {
      "id": 5,
      "namespace": "network",
      "function": "connections",
      "arguments": [],
      "category": "network"
    },
    {
      "id": 6,
      "namespace": "network",
      "function": "routes",
      "arguments": [],
      "category": "network"
    },
    {
      "id": 7,
      "namespace": "network",
      "function": "dns",
      "arguments": [],
      "category": "network"
    },
    {
      "id": 8,
      "namespace": "filesystem",
      "function": "metadata",
      "arguments": [
        "./evidence"
      ],
      "category": "filesystem"
    },
    {
      "id": 9,
      "namespace": "filesystem",
      "function": "hash",
      "arguments": [
        "./evidence"
      ],
      "category": "filesystem"
    }
  ]
}
```

---

## 5. How Proteus Agents Consume JOCKY IR

```
 ┌────────────────────────────────────────┐
 │           Proteus Manager              │
 └───────────────────┬────────────────────┘
                     │  Forensic IR (JSON)
                     ▼
 ┌────────────────────────────────────────┐
 │    Proteus Agent (Windows / Ubuntu)    │
 └───────────────────┬────────────────────┘
                     │
       ┌─────────────┴─────────────┐
       ▼                           ▼
 ┌───────────────┐           ┌───────────────┐
 │ Process Loop  │           │ Dispatcher    │
 └───────┬───────┘           └───────┬───────┘
         │                           │
         ▼                           ▼
 ┌───────────────────────────────────────────┐
 │ Native OS Collectors (Win32 / Linux Proc) │
 └───────────────────┬───────────────────────┘
                     │ Telemetry Payload
                     ▼
 ┌───────────────────────────────────────────┐
 │ Encrypted Telemetry Report (Signed)       │
 └───────────────────────────────────────────┘
```

1. **Agent Fetch**: Agent receives the JSON IR payload from the Proteus Manager.
2. **Sequential Dispatch**: Agent processes each operation in ascending order of `id`.
3. **Execution**: The agent invokes its internal native collector matching the `category`, `namespace`, and `function`.
4. **Result Bundling**: Telemetry is tagged with the corresponding operation `id` and returned for analyst review.
