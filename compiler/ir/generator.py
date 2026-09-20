"""
Forensic IR Generator for JOCKY.
Translates a semantically validated AST into deterministic JOCKY IR (IRDocument).
"""
from typing import Optional, List

try:
    from compiler.parser.ast import Program, AnalysisBlock, FunctionCall
    from compiler.ir.model import IRDocument, IROperation, IRValidationError
    from compiler.semantic.registry import ForensicFunctionRegistry, DEFAULT_REGISTRY
except (ImportError, ModuleNotFoundError):
    from parser.ast import Program, AnalysisBlock, FunctionCall
    from ir.model import IRDocument, IROperation, IRValidationError
    from semantic.registry import ForensicFunctionRegistry, DEFAULT_REGISTRY


class IRGenerator:
    def __init__(self, registry: Optional[ForensicFunctionRegistry] = None):
        self.registry = registry or DEFAULT_REGISTRY

    def generate(self, ast: Program) -> IRDocument:
        """
        Generates deterministic JOCKY IR (IRDocument) from a validated AST.
        """
        if not isinstance(ast, Program):
            raise IRValidationError(f"Expected Program AST node, got {type(ast).__name__}.")

        analyses = [decl for decl in ast.body if isinstance(decl, AnalysisBlock)]
        if not analyses:
            return IRDocument(
                investigation="Empty Investigation",
                operations=[],
                version="1.0",
                ir_type="jocky_forensic_ir",
            )

        # Generate IR for the primary analysis block
        decl = analyses[0]
        return self._generate_analysis(decl)

    def _generate_analysis(self, decl: AnalysisBlock) -> IRDocument:
        operations: List[IROperation] = []
        op_id = 1

        for stmt in decl.statements:
            if isinstance(stmt, FunctionCall):
                op_type = f"{stmt.namespace}.{stmt.function}"
                spec = self.registry.get_function_spec(stmt.namespace, stmt.function)

                if spec is None:
                    raise IRValidationError(f"Cannot generate IR for unknown forensic function '{op_type}'.")

                # Map positional AST arguments to named parameter dictionary defined by the registry
                parameters = {}
                if spec.arguments:
                    for arg_spec, arg_node in zip(spec.arguments, stmt.arguments):
                        parameters[arg_spec.name] = arg_node.value

                op = IROperation(
                    id=f"op-{op_id:03d}",
                    type=op_type,
                    parameters=parameters,
                )
                operations.append(op)
                op_id += 1

        return IRDocument(
            investigation=decl.name,
            operations=operations,
            version="1.0",
            ir_type="jocky_forensic_ir",
        )
