"""
JOCKY Compiler Pipeline
Provides the unified compile() and check() interfaces and CompilationResult.
"""
from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Optional

try:
    from compiler.diagnostics.diagnostics import Diagnostic, DiagnosticReporter
    from compiler.lexer.tokenizer import Lexer
    from compiler.lexer.tokens import Token
    from compiler.parser.ast import Program
    from compiler.parser.parser import Parser
    from compiler.semantic.analyzer import SemanticAnalyzer
    from compiler.semantic.registry import ForensicFunctionRegistry, DEFAULT_REGISTRY
    from compiler.ir.generator import IRGenerator
    from compiler.ir.model import ForensicIRDocument
except (ImportError, ModuleNotFoundError):
    from diagnostics.diagnostics import Diagnostic, DiagnosticReporter
    from lexer.tokenizer import Lexer
    from lexer.tokens import Token
    from parser.ast import Program
    from parser.parser import Parser
    from semantic.analyzer import SemanticAnalyzer
    from semantic.registry import ForensicFunctionRegistry, DEFAULT_REGISTRY
    from ir.generator import IRGenerator
    from ir.model import ForensicIRDocument


@dataclass
class CompilationResult:
    success: bool
    tokens: List[Token] = field(default_factory=list)
    ast: Optional[Program] = None
    ir: Optional[Dict[str, Any]] = None
    diagnostics: List[Diagnostic] = field(default_factory=list)
    source: str = ""
    filename: str = "<input>"

    def to_dict(self) -> dict:
        d = {
            "success": self.success,
            "diagnostics": [diag.to_dict() for diag in self.diagnostics],
            "ast": self.ast.to_dict() if self.ast is not None else None,
            "ir": self.ir,
        }
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def format_diagnostics(self) -> str:
        reporter = DiagnosticReporter(self.source, self.filename)
        for d in self.diagnostics:
            reporter.add(d)
        return reporter.format_all()


class Compiler:
    def __init__(self, registry: Optional[ForensicFunctionRegistry] = None):
        self.registry = registry or DEFAULT_REGISTRY

    def compile(self, source: str, filename: str = "<input>") -> CompilationResult:
        """
        Compiles JOCKY source code through the full pipeline:
        source -> lexer -> parser -> semantic analysis -> IR generation
        """
        reporter = DiagnosticReporter(source, filename)

        # 1. Lexical Analysis
        lexer = Lexer(source, filename, reporter)
        tokens = lexer.tokenize()
        if reporter.has_errors():
            return CompilationResult(
                success=False,
                tokens=tokens,
                diagnostics=reporter.diagnostics,
                source=source,
                filename=filename,
            )

        # 2. Parsing & AST Generation
        parser = Parser(tokens, source, filename, reporter)
        ast = parser.parse()
        if reporter.has_errors():
            return CompilationResult(
                success=False,
                tokens=tokens,
                ast=ast,
                diagnostics=reporter.diagnostics,
                source=source,
                filename=filename,
            )

        # 3. Semantic Analysis
        analyzer = SemanticAnalyzer(self.registry, source, filename, reporter)
        analyzer.analyze(ast)
        if reporter.has_errors():
            return CompilationResult(
                success=False,
                tokens=tokens,
                ast=ast,
                diagnostics=reporter.diagnostics,
                source=source,
                filename=filename,
            )

        # 4. IR Generation
        ir_gen = IRGenerator(self.registry)
        ir_doc = ir_gen.generate(ast)
        ir_dict = ir_doc.to_dict()

        return CompilationResult(
            success=True,
            tokens=tokens,
            ast=ast,
            ir=ir_dict,
            diagnostics=[],
            source=source,
            filename=filename,
        )

    def check(self, source: str, filename: str = "<input>") -> CompilationResult:
        """
        Verifies syntax, AST generation, and semantics without IR generation.
        """
        reporter = DiagnosticReporter(source, filename)

        lexer = Lexer(source, filename, reporter)
        tokens = lexer.tokenize()
        if reporter.has_errors():
            return CompilationResult(
                success=False,
                tokens=tokens,
                diagnostics=reporter.diagnostics,
                source=source,
                filename=filename,
            )

        parser = Parser(tokens, source, filename, reporter)
        ast = parser.parse()
        if reporter.has_errors():
            return CompilationResult(
                success=False,
                tokens=tokens,
                ast=ast,
                diagnostics=reporter.diagnostics,
                source=source,
                filename=filename,
            )

        analyzer = SemanticAnalyzer(self.registry, source, filename, reporter)
        analyzer.analyze(ast)

        return CompilationResult(
            success=not reporter.has_errors(),
            tokens=tokens,
            ast=ast,
            diagnostics=reporter.diagnostics,
            source=source,
            filename=filename,
        )


def compile(source: str, filename: str = "<input>") -> CompilationResult:
    """Convenience functional interface for compilation."""
    return Compiler().compile(source, filename)


def check(source: str, filename: str = "<input>") -> CompilationResult:
    """Convenience functional interface for syntax and semantics checking."""
    return Compiler().check(source, filename)
