"""
Forensic IR Generator for JOCKY.
Translates a semantically validated AST into deterministic Forensic IR.
"""
from typing import Optional

try:
    from compiler.parser.ast import Program, AnalysisBlock, FunctionCall
    from compiler.ir.model import ForensicIROperation, ForensicIRAnalysis, ForensicIRDocument
    from compiler.semantic.registry import ForensicFunctionRegistry, DEFAULT_REGISTRY
except (ImportError, ModuleNotFoundError):
    from parser.ast import Program, AnalysisBlock, FunctionCall
    from ir.model import ForensicIROperation, ForensicIRAnalysis, ForensicIRDocument
    from semantic.registry import ForensicFunctionRegistry, DEFAULT_REGISTRY


class IRGenerator:
    def __init__(self, registry: Optional[ForensicFunctionRegistry] = None):
        self.registry = registry or DEFAULT_REGISTRY

    def generate(self, ast: Program) -> ForensicIRDocument:
        """
        Generates deterministic Forensic IR from an AST.
        """
        analyses = []
        for decl in ast.body:
            if isinstance(decl, AnalysisBlock):
                analysis_ir = self._generate_analysis(decl)
                analyses.append(analysis_ir)

        return ForensicIRDocument(analyses=analyses)

    def _generate_analysis(self, decl: AnalysisBlock) -> ForensicIRAnalysis:
        operations = []
        op_id = 1

        for stmt in decl.statements:
            if isinstance(stmt, FunctionCall):
                args = [arg.value for arg in stmt.arguments]
                
                # Determine category from registry
                spec = self.registry.get_function_spec(stmt.namespace, stmt.function)
                category = spec.category if spec else stmt.namespace

                op = ForensicIROperation(
                    id=op_id,
                    namespace=stmt.namespace,
                    function=stmt.function,
                    arguments=args,
                    category=category,
                )
                operations.append(op)
                op_id += 1

        return ForensicIRAnalysis(
            name=decl.name,
            operations=operations,
            version="1.0",
            type="forensic_analysis",
        )
