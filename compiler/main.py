#!/usr/bin/env python3
import sys
import argparse
from lexer.tokenizer import Lexer
from parser.parser import Parser

def compile_file(filepath):
    """Compile a JOCKY source file"""
    with open(filepath, 'r') as f:
        source = f.read()
    
    # Lexical analysis
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    print(f"✅ Tokenized successfully: {len(tokens)} tokens")
    
    # Parsing
    parser = Parser(tokens)
    ast = parser.parse()
    print(f"✅ Parsed successfully: AST generated")
    
    # TODO: LLVM Code Generation
    print("⏳ LLVM Code Generation (coming soon!)")
    
    return ast

def main():
    parser = argparse.ArgumentParser(description='JOCKY Compiler')
    parser.add_argument('command', choices=['compile'], help='Command to execute')
    parser.add_argument('file', help='Input JOCKY file (.jky)')
    parser.add_argument('--output', '-o', help='Output file path')
    
    args = parser.parse_args()
    
    if args.command == 'compile':
        compile_file(args.file)

if __name__ == "__main__":
    main()