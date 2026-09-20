#!/usr/bin/env python3
"""
JOCKY Compiler – Command Line Interface
Forensic Scripting Language Compiler & Diagnostic Tool.
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Support running directly or as a module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from compiler.compiler import Compiler, compile as jocky_compile, check as jocky_check


def print_banner():
    print("====================================")
    print("          JOCKY COMPILER            ")
    print("====================================\n")


def cmd_compile(args):
    filepath = args.file
    if not os.path.isfile(filepath):
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    print_banner()
    print(f"Source:\n{filepath}\n")

    compiler = Compiler()
    result = compiler.compile(source, filename=filepath)

    if not result.success:
        print(result.format_diagnostics(), file=sys.stderr)
        print("\nCompilation failed.", file=sys.stderr)
        sys.exit(1)

    print("✓ Lexical analysis")
    print("✓ Parsing")
    print("✓ AST generation")
    print("✓ Semantic validation")
    print("✓ IR generation")

    ir_data = result.ir or {}
    analysis_name = ir_data.get("investigation") or ir_data.get("name", "Unknown")
    operations = ir_data.get("operations", [])

    print(f"\nAnalysis:\n{analysis_name}")
    print(f"\nOperations:\n{len(operations)}")
    print("\nCompilation successful.")

    # Determine output path
    if args.output:
        out_path = Path(args.output)
    else:
        basename = Path(filepath).stem
        build_dir = Path("build")
        build_dir.mkdir(parents=True, exist_ok=True)
        out_path = build_dir / f"{basename}.ir.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(ir_data, f, indent=2)

    print(f"\nGenerated:\n{out_path}")

    # Inspect flags
    if args.ast and result.ast:
        print("\n---------------- AST ----------------")
        print(json.dumps(result.ast.to_dict(), indent=2))
        print("-------------------------------------")

    if args.ir and result.ir:
        print("\n---------------- IR -----------------")
        print(json.dumps(result.ir, indent=2))
        print("-------------------------------------")


def cmd_check(args):
    filepath = args.file
    if not os.path.isfile(filepath):
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    print_banner()
    print(f"Source:\n{filepath}\n")

    result = jocky_check(source, filename=filepath)

    if not result.success:
        print(result.format_diagnostics(), file=sys.stderr)
        print("\nCheck failed with errors.", file=sys.stderr)
        sys.exit(1)

    print("✓ Lexical analysis")
    print("✓ Parsing")
    print("✓ AST generation")
    print("✓ Semantic validation")
    print("\nCompilation successful.")

    if args.ast and result.ast:
        print("\n---------------- AST ----------------")
        print(json.dumps(result.ast.to_dict(), indent=2))
        print("-------------------------------------")


def main():
    parser = argparse.ArgumentParser(
        prog="jocky",
        description="JOCKY Forensic Scripting Language Compiler",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # compile subcommand
    compile_parser = subparsers.add_parser("compile", help="Compile JOCKY source to Forensic IR")
    compile_parser.add_argument("file", help="Path to .jocky source file")
    compile_parser.add_argument("--output", "-o", help="Custom output path for generated IR JSON")
    compile_parser.add_argument("--ast", action="store_true", help="Print readable AST JSON to stdout")
    compile_parser.add_argument("--ir", action="store_true", help="Print generated IR JSON to stdout")

    # check subcommand
    check_parser = subparsers.add_parser("check", help="Verify syntax and semantics without generating IR")
    check_parser.add_argument("file", help="Path to .jocky source file")
    check_parser.add_argument("--ast", action="store_true", help="Print readable AST JSON to stdout")

    args = parser.parse_args()

    if args.command == "compile":
        cmd_compile(args)
    elif args.command == "check":
        cmd_check(args)


if __name__ == "__main__":
    main()