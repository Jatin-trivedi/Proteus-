#!/usr/bin/env python3
"""
JOCKY Compiler – Main Entry Point
Supports CLI compilation and in‑memory byte generation for Member F.
"""

import sys
import argparse
import os
import subprocess
import tempfile
import hashlib
from lexer.tokenizer import Lexer
from parser.parser import Parser
from codegen.llvm_gen import compile_to_llvm, generate_llvm_ir
from cache import compiler_cache


def compile_to_bytes(source_code: str) -> bytes:
    """
    Compile JOCKY source code (string) to an executable (.exe) and return the
    binary as bytes. Uses a temporary directory; no disk persistence.
    This is the main function for Member F (orchestrator) to get .exe bytes.
    """
    # 1. Lexical analysis
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    print(f"[Compiler] Tokenized: {len(tokens)} tokens")

    # 2. Parsing
    parser = Parser(tokens)
    ast = parser.parse()
    print("[Compiler] Parsed: AST generated")

    # 3. Generate LLVM IR and compile to executable inside a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        ll_file = os.path.join(tmpdir, "output.ll")
        exe_file = os.path.join(tmpdir, "output.exe")

        # Generate LLVM IR
        ir_code = generate_llvm_ir(ast)
        with open(ll_file, 'w') as f:
            f.write(ir_code)
        print(f"[Compiler] LLVM IR written to {ll_file}")

        # Use clang to compile .ll to .exe
        try:
            subprocess.run(
                ["clang", "-O2", "-o", exe_file, ll_file],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            print(f"[Compiler] Clang error: {e.stderr}")
            raise RuntimeError(f"Clang compilation failed: {e.stderr}")

        # Read the .exe bytes
        with open(exe_file, 'rb') as f:
            exe_bytes = f.read()

    print(f"[Compiler] Compiled .exe size: {len(exe_bytes)} bytes")
    return exe_bytes


def compile_file(filepath: str, output_file: str = None) -> bytes:
    """
    CLI‑compatible function: reads a .jky file, compiles it, and writes the
    .exe to disk. Returns the bytes for convenience.
    """
    with open(filepath, 'r') as f:
        source = f.read()

    # Use the in‑memory compiler
    exe_bytes = compile_to_bytes(source)

    # Write to disk
    if not output_file:
        basename = os.path.splitext(filepath)[0]
        output_file = f"{basename}.exe" if os.name == 'nt' else basename

    with open(output_file, 'wb') as f:
        f.write(exe_bytes)
    print(f"[Compiler] Written to {output_file}")

    # Cache the AST (optional – we could cache the hash of source)
    ast = None  # we don't have AST here, but we could re‑parse if needed
    compiler_cache.set(source, {"tokens": 0, "ast": "cached"})

    return exe_bytes


def main():
    parser = argparse.ArgumentParser(description='JOCKY Compiler')
    parser.add_argument('command', choices=['compile'], help='Command to execute')
    parser.add_argument('file', help='Input JOCKY file (.jky)')
    parser.add_argument('--output', '-o', help='Output file path')

    args = parser.parse_args()

    if args.command == 'compile':
        compile_file(args.file, args.output)


if __name__ == "__main__":
    main()