#!/usr/bin/env python3
"""
JOCKY Compiler – Main Entry Point
Universal Edition - Supports all features via `run()` and `system()`
"""
import sys
import argparse
import os
import subprocess
import tempfile
from lexer.tokenizer import Lexer
from parser.parser import Parser
from codegen.llvm_gen import generate_llvm_ir, get_jocky_c_runtime

def compile_to_bytes(source_code: str) -> bytes:
    # 1. Lexical analysis
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    print(f"[Compiler] Tokenized: {len(tokens)} tokens")

    # 2. Parsing
    parser = Parser(tokens)
    ast = parser.parse()
    print("[Compiler] Parsed: AST generated")

    # Extract agent name
    agent_name = "jocky_main"
    for stmt in ast.body:
        if hasattr(stmt, 'name'):
            agent_name = stmt.name
            break

    # 3. Generate LLVM IR
    with tempfile.TemporaryDirectory() as tmpdir:
        ll_file = os.path.join(tmpdir, "output.ll")
        obj_file = os.path.join(tmpdir, "output.o")
        c_file = os.path.join(tmpdir, "output_runtime.c")
        c_obj = os.path.join(tmpdir, "output_runtime.o")
        exe_file = os.path.join(tmpdir, "output.exe")

        # Generate LLVM IR
        ir_code = generate_llvm_ir(ast)
        with open(ll_file, 'w') as f:
            f.write(ir_code)

        # 4. Compile LLVM to object file
        subprocess.run(["llc", "-mtriple", "x86_64-pc-windows-gnu", "-filetype=obj", ll_file, "-o", obj_file], check=True, capture_output=True, text=True)

        # 5. Create C runtime (Universal Bridge)
        c_code = get_jocky_c_runtime(agent_name)
        with open(c_file, 'w') as f:
            f.write(c_code)

        # 6. Compile C runtime to object
        subprocess.run(["gcc", "-c", c_file, "-o", c_obj], check=True, capture_output=True, text=True)

        # 7. Link
        subprocess.run(["gcc", "-mconsole", "-o", exe_file, obj_file, c_obj], check=True, capture_output=True, text=True)

        # 8. Return bytes
        with open(exe_file, 'rb') as f:
            exe_bytes = f.read()

    print(f"[Compiler] Compiled .exe size: {len(exe_bytes)} bytes")
    return exe_bytes

def compile_file(filepath: str, output_file: str = None) -> bytes:
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    exe_bytes = compile_to_bytes(source)

    if not output_file:
        basename = os.path.splitext(filepath)[0]
        output_file = f"{basename}.exe" if os.name == 'nt' else basename

    with open(output_file, 'wb') as f:
        f.write(exe_bytes)
    print(f"[Compiler] Written to {output_file}")
    return exe_bytes

def main():
    parser = argparse.ArgumentParser(description='JOCKY Compiler')
    parser.add_argument('command', choices=['compile'])
    parser.add_argument('file')
    parser.add_argument('--output', '-o')
    args = parser.parse_args()
    if args.command == 'compile':
        compile_file(args.file, args.output)

if __name__ == "__main__":
    main()