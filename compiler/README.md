# JOCKY Compiler

The JOCKY compiler converts forensic analysis source files into a validated,
deterministic intermediate representation (IR). It is designed for controlled,
read-only forensic collection and does not provide arbitrary shell execution,
dynamic evaluation, persistence, or exploit operations.

## Requirements

- Python 3.11 or newer
- Dependencies listed in `requirements.txt`
- The repository root on `PYTHONPATH` when invoking the compiler as a module

Install the compiler dependencies from the repository root:

```bash
python -m pip install -r compiler/requirements.txt
```

## Source File Format

JOCKY programs contain one or more named `analysis` blocks. Each statement is
an approved forensic function call followed by a semicolon:

```jocky
analysis "Process Investigation" {
    system.info();
    processes.list();
    network.connections();
    filesystem.hash("./evidence");
}
```

Arguments may be string, number, or boolean literals. Variables declared
earlier in the same analysis block can also be used:

```jocky
analysis "Targeted Investigation" {
    let pid = 1234;
    processes.details(pid);
    let collect_network = true && true;
}
```

Single-line comments use `#` or `//`.

## Approved Forensic Functions

| Namespace | Function | Arguments | Purpose |
|:---|:---|:---|:---|
| `system` | `info()` | None | Collect host and operating-system information |
| `system` | `users()` | None | Collect local user and session information |
| `processes` | `list()` | None | List running processes |
| `processes` | `details(pid)` | Number | Collect details for one process |
| `network` | `interfaces()` | None | Collect network adapter information |
| `network` | `connections()` | None | Collect active network connections |
| `network` | `routes()` | None | Collect routing information |
| `network` | `dns()` | None | Collect DNS configuration and cache information |
| `filesystem` | `metadata(path)` | String | Collect file metadata |
| `filesystem` | `hash(path)` | String | Calculate a file or directory hash |

Unknown namespaces, functions, argument counts, and argument types are rejected
during semantic analysis.

## Compiler Pipeline

```text
Source (.jocky)
    |
    v
Lexer             -> token stream
    |
    v
Parser            -> abstract syntax tree (AST)
    |
    v
Semantic analyzer -> scope, type, and registry validation
    |
    v
IR generator      -> deterministic forensic IR JSON
    |
    v
CompilationResult -> diagnostics, AST, and IR
```

The main implementation is in:

- `lexer/` — tokenization
- `parser/` — syntax and AST construction
- `semantic/` — registry and semantic checks
- `ir/` — IR models, generation, and validation
- `diagnostics/` — source locations and compiler messages
- `builtins/` — supported forensic function signatures and test helpers

The manager uses the same compiler pipeline before a script deployment is
created. Invalid JOCKY source is rejected instead of being passed to an
endpoint as a command.

## Command-Line Usage

Run these commands from the repository root:

```bash
# Compile source into forensic IR
python -m compiler compile path/to/investigation.jocky

# Check syntax and semantics without generating IR
python -m compiler check path/to/investigation.jocky
```

The command-line interface is implemented in [`main.py`](main.py). The
programmatic interface is available through `compiler.Compiler`, `compile()`,
and `check()` in [`compiler.py`](compiler.py).

## Generated IR

The generated document preserves source order and contains the analysis name
plus an ordered list of approved operations:

```json
{
  "version": "1.0",
  "type": "forensic_analysis",
  "name": "Process Investigation",
  "operations": [
    {
      "id": 1,
      "namespace": "processes",
      "function": "list",
      "arguments": [],
      "category": "process"
    }
  ]
}
```

See [`docs/JOCKY_LANGUAGE.md`](../docs/JOCKY_LANGUAGE.md) for the language
reference and [`docs/JOCKY_IR.md`](../docs/JOCKY_IR.md) for the complete IR
schema.

## Tests

From the repository root:

```bash
python -m pytest compiler/tests/ -v
```
