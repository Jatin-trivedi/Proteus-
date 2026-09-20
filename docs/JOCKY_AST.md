# JOCKY Abstract Syntax Tree (AST)

## 1. Overview
The **JOCKY AST** is the structured in-memory syntax representation produced by the recursive-descent parser during compilation. It represents the hierarchical structure of a forensic analysis script without any syntactic ambiguities.

---

## 2. AST Hierarchy & Node Types

### Node Hierarchy
```
Program
└── AnalysisBlock (one or more)
    ├── name: string
    └── statements: list[FunctionCall]
        └── FunctionCall
            ├── namespace: string
            ├── function: string
            └── arguments: list[Argument]
                └── Argument
                    ├── value: string | number | boolean
                    └── arg_type: "string" | "number" | "boolean"
```

### Core Node Classes

| Node Class | Properties | Description |
|---|---|---|
| `Program` | `analyses: list[AnalysisBlock]` | Root node representing the entire JOCKY script file. |
| `AnalysisBlock` | `name: str`, `statements: list[FunctionCall]` | Represents an `analysis "Name" { ... }` block. |
| `FunctionCall` | `namespace: str`, `function: str`, `arguments: list[Argument]` | Represents a forensic collector call (e.g. `system.info()`). |
| `Argument` | `value: Any`, `arg_type: str` | Represents a literal argument passed to a function call. |

---

## 3. Serialization Schema

Every AST node implements `.to_dict()` and `.to_json()` for debugging, tool integration, and serialization.

### Example JOCKY Source
```jocky
analysis "Network Investigation" {
    network.interfaces();
    network.connections();
    network.dns();
}
```

### Serialized AST JSON
```json
{
  "type": "Program",
  "analyses": [
    {
      "type": "AnalysisBlock",
      "name": "Network Investigation",
      "statements": [
        {
          "type": "FunctionCall",
          "namespace": "network",
          "function": "interfaces",
          "arguments": []
        },
        {
          "type": "FunctionCall",
          "namespace": "network",
          "function": "connections",
          "arguments": []
        },
        {
          "type": "FunctionCall",
          "namespace": "network",
          "function": "dns",
          "arguments": []
        }
      ]
    }
  ]
}
```

---

## 4. Source Location Tracking
All AST nodes preserve original source code location metadata:
- `line` (*int*): 1-based source line number.
- `column` (*int*): 1-based source column index.
- `offset` (*int*): 0-based character position in the source stream.

This enables precise diagnostic pointing during the subsequent semantic validation phase.
