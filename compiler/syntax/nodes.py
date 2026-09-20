"""
Syntax nodes for JOCKY AST.
Re-exported from parser.ast for backward compatibility.
"""
try:
    from compiler.parser.ast import *
except (ImportError, ModuleNotFoundError):
    from parser.ast import *