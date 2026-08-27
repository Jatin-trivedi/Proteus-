#!/usr/bin/env python3
import sys
import argparse
import os
from lexer.tokenizer import Lexer
from parser.parser import Parser
from codegen.llvm_gen import compile_to_llvm
from cache import compiler_cache

def compile_file(filepath, output_file=None):
    with open(filepath, 'r') as f:
        source = f.read()
    
    # Check cache
    cached = compiler_cache.get(source)
    if cached:
        print(f"✅ Using cached compilation")
        return cached["ast"]
    
    # Lexical analysis
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    print(f"✅ Tokenized successfully: {len(tokens)} tokens")
    
    # Parsing
    parser = Parser(tokens)
    ast = parser.parse()
    print(f"✅ Parsed successfully: AST generated")
    
    # LLVM Code Generation
    print(f"⏳ Generating LLVM IR...")
    
    if not output_file:
        basename = os.path.splitext(filepath)[0]
        output_file = f"{basename}.exe" if os.name == 'nt' else basename
    
    ir_code = compile_to_llvm(ast, output_file)
    print(f"✅ LLVM IR generated successfully")
    
    # Cache the AST
    compiler_cache.set(source, {"tokens": len(tokens), "ast": str(ast)})
    
    return ast

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