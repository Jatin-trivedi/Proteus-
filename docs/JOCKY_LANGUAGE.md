# JOCKY Forensic Scripting Language

## 1. Overview & Purpose
**JOCKY** is a specialized, domain-specific forensic analysis scripting language engineered for the **Proteus** digital forensics and incident response (DFIR) platform. 

JOCKY empowers incident responders, forensic analysts, and automated detection pipelines to express controlled, deterministic triage investigations without exposing endpoints to arbitrary execution risks.

---

## 2. Design Goals & Safety Guarantees

### Safety by Design
Unlike general-purpose scripting languages (Python, PowerShell, Bash), JOCKY is explicitly **defensive and non-arbitrary**:
- ❌ **No Arbitrary Shell/Command Execution**: There is no `exec()`, `spawn()`, `system()`, or shell evaluation.
- ❌ **No Code Injection / Dynamic Eval**: Commands cannot be constructed dynamically at runtime.
- ❌ **No Credential Dumping / Exploit Payloads**: Cannot invoke unauthorized OS APIs or memory injectors.
- ❌ **No Persistence / Security Evasion**: Operations are strictly read-only or authorized forensic artifacts collection.

### Determinism
- JOCKY scripts compile down to deterministic **Forensic Intermediate Representation (IR)** in JSON format.
- Given the same source code, the compiler always yields an identical, ordered sequence of forensic operations.

---

## 3. Language Syntax & Grammar

### Grammar (EBNF)
```ebnf
program             := analysis_declaration+

analysis_declaration := "analysis" STRING "{" statement* "}"

statement           := function_call ";"

function_call       := IDENTIFIER "." IDENTIFIER "(" arguments? ")"

arguments           := expression ("," expression)*

expression          := STRING | NUMBER | BOOLEAN
```

### Comments
JOCKY supports both `#` and `//` style single-line comments:
```jocky
# Full line comment
analysis "Triage Example" {
    // Collect host info
    system.info();
    system.users(); # Local user enumeration
}
```

---

## 4. Forensic Namespaces & Collectors

All operations in JOCKY map directly to approved collectors organized into four core namespaces:

| Namespace | Function | Arguments | Description |
|---|---|---|---|
| `system` | `info()` | *(none)* | Gathers core host metadata (OS, hostname, architecture, uptime, kernel). |
| `system` | `users()` | *(none)* | Enumerates local user accounts, active sessions, and privilege levels. |
| `processes` | `list()` | *(none)* | Lists running processes (PID, PPID, executable path, username, memory). |
| `processes` | `details(pid)` | `pid: number` | Deep forensic inspection of a process (threads, handles, loaded DLLs, env). |
| `network` | `interfaces()` | *(none)* | Enumerates network adapters, MAC addresses, IPv4/IPv6 addresses, link status. |
| `network` | `connections()` | *(none)* | Lists active TCP/UDP network connections, listening sockets, and PIDs. |
| `network` | `routes()` | *(none)* | Dumps kernel IP routing tables and gateway configurations. |
| `network` | `dns()` | *(none)* | Extracts local DNS cache, resolver configuration, and DNS query history. |
| `filesystem` | `metadata(path)` | `path: string` | Gathers timestamps (MACB), permissions, owner, and attributes for a path. |
| `filesystem` | `hash(path)` | `path: string` | Computes cryptographic hashes (SHA-256, MD5) of the target file or directory. |

---

## 5. Compiler Pipeline

```
 Source Code (.jocky)
         │
         ▼
 ┌───────────────┐
 │     Lexer     │  --> Token stream with line, column, and offset tracking
 └───────┬───────┘
         ▼
 ┌───────────────┐
 │    Parser     │  --> Abstract Syntax Tree (AST)
 └───────┬───────┘
         ▼
 ┌───────────────┐
 │   Semantic    │  --> Namespace, function, argument count & type validation
 │   Analyzer    │      via ForensicFunctionRegistry
 └───────┬───────┘
         ▼
 ┌───────────────┐
 │  IR Generator │  --> Deterministic Forensic IR Document (JSON)
 └───────┬───────┘
         ▼
   CompilationResult (success, tokens, ast, ir, diagnostics)
```

---

## 6. Error Diagnostics & Codes

JOCKY provides Clang/Rust-style formatted diagnostic messages with exact source code pointers:

```
JOCKY-E2001: Unknown forensic function 'system.fakeFunction'
  --> language/examples/invalid.jocky:3:5
   3 |     system.fakeFunction();
     |     ^^^^^^^^^^^^^^^^^^^
      help: Available functions in 'system':
            - system.info()
            - system.users()
```

### Diagnostic Code Reference

| Code | Severity | Description |
|---|---|---|
| `JOCKY-E1000` | Error | Unexpected character during lexical analysis |
| `JOCKY-E1001` | Error | Unterminated string literal |
| `JOCKY-E1002` | Error | Invalid numeric literal |
| `JOCKY-E1100` | Error | General syntax error |
| `JOCKY-E1101` | Error | Expected semicolon `;` |
| `JOCKY-E1102` | Error | Expected opening brace `{` |
| `JOCKY-E1103` | Error | Expected closing brace `}` |
| `JOCKY-E1104` | Error | Expected opening parenthesis `(` |
| `JOCKY-E1105` | Error | Expected closing parenthesis `)` |
| `JOCKY-E1106` | Error | Expected identifier |
| `JOCKY-E1107` | Error | Expected string literal |
| `JOCKY-E1108` | Error | Malformed function call |
| `JOCKY-E1109` | Error | Expected `analysis` declaration block |
| `JOCKY-E2001` | Error | Unknown forensic function in namespace |
| `JOCKY-E2002` | Error | Function argument count mismatch |
| `JOCKY-E2003` | Error | Argument type mismatch (e.g. expected string, got number) |
| `JOCKY-E2004` | Error | Unknown forensic namespace |

---

## 7. CLI Usage

### Compiling to Forensic IR
```bash
# Compile and output to build/<name>.ir.json
python -m compiler compile language/examples/system.jocky

# Compile to custom output path
python -m compiler compile language/examples/system.jocky -o custom_output.json
```

### Checking Syntax & Semantics
```bash
python -m compiler check language/examples/system.jocky
```

---

## 8. Examples

### System Investigation (`language/examples/system.jocky`)
```jocky
analysis "System Investigation" {
    system.info();
    system.users();
    processes.list();
    network.interfaces();
    network.connections();
    filesystem.hash("./evidence");
}
```

### Network Investigation (`language/examples/network.jocky`)
```jocky
analysis "Network Investigation" {
    network.interfaces();
    network.connections();
    network.routes();
    network.dns();
}
```
