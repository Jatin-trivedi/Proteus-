# JOCKY Compiler

Converts JOCKY language source files (`.jky`) to LLVM IR and native binaries.

## Usage

```

Analysis arguments may be literals or variables declared earlier in the
analysis block. Logical expressions support `&&` and `||`.

```jocky
analysis "Process Investigation" {
    let pid = 1234;
    processes.details(pid);
    let collect_network = true && true;
}
```bash
python main.py compile <script.jky>