"""
Semantic Analyzer for JOCKY.
Validates namespaces, forensic functions, argument counts, and argument types against the ForensicFunctionRegistry.
"""
from typing import Any, Dict, Optional, Tuple

try:
    from compiler.parser.ast import Program, AnalysisBlock, FunctionCall, Argument, LetStatement, BinaryOperation, Identifier
    from compiler.semantic.registry import ForensicFunctionRegistry, DEFAULT_REGISTRY
    from compiler.diagnostics.diagnostics import DiagnosticReporter, DiagnosticCode
except (ImportError, ModuleNotFoundError):
    from parser.ast import Program, AnalysisBlock, FunctionCall, Argument, LetStatement, BinaryOperation, Identifier
    from semantic.registry import ForensicFunctionRegistry, DEFAULT_REGISTRY
    from diagnostics.diagnostics import DiagnosticReporter, DiagnosticCode


class SemanticAnalyzer:
    def __init__(
        self,
        registry: Optional[ForensicFunctionRegistry] = None,
        source: str = "",
        filename: str = "<input>",
        reporter: Optional[DiagnosticReporter] = None,
    ):
        self.registry = registry or DEFAULT_REGISTRY
        self.source = source
        self.filename = filename
        self.reporter = reporter or DiagnosticReporter(source, filename)

    def analyze(self, ast: Program) -> bool:
        """
        Performs semantic analysis on the AST.
        Returns True if analysis succeeded with no errors, False otherwise.
        """
        for declaration in ast.body:
            if isinstance(declaration, AnalysisBlock):
                self._analyze_analysis_block(declaration)
        return not self.reporter.has_errors()

    def _analyze_analysis_block(self, decl: AnalysisBlock):
        scope: Dict[str, Tuple[Any, str]] = {}
        for stmt in decl.statements:
            if isinstance(stmt, LetStatement):
                value = self._resolve_expression(stmt.value, scope)
                if value is not None:
                    scope[stmt.name] = value
            elif isinstance(stmt, FunctionCall):
                self._analyze_function_call(stmt, scope)

    def _analyze_function_call(self, call: FunctionCall, scope: Optional[Dict[str, Tuple[Any, str]]] = None):
        scope = scope or {}
        namespace = call.namespace
        function = call.function

        # 1. Validate Namespace (JOCKY-E2001)
        if not self.registry.has_namespace(namespace):
            available_ns = ", ".join(self.registry.get_all_namespaces())
            self.reporter.error(
                code=DiagnosticCode.UNKNOWN_NAMESPACE,
                message=f"Unknown namespace '{namespace}'.",
                line=call.line,
                column=call.column,
                offset=call.offset,
                length=len(namespace),
                help_text=f"Available namespaces: {available_ns}",
            )
            return

        # 2. Validate Function in Namespace (JOCKY-E2002)
        if not self.registry.has_function(namespace, function):
            available_funcs = self.registry.get_available_functions(namespace)
            formatted_funcs = "\n".join(f"{namespace}.{f}()" for f in available_funcs)
            self.reporter.error(
                code=DiagnosticCode.UNKNOWN_FUNCTION,
                message=f"Unknown forensic function '{namespace}.{function}'.",
                line=call.line,
                column=call.column,
                offset=call.offset,
                length=len(namespace) + 1 + len(function),
                help_text=f"Available functions:\n{formatted_funcs}",
            )
            return

        spec = self.registry.get_function_spec(namespace, function)
        if not spec:
            return

        actual_arg_count = len(call.arguments)

        # 3. Missing Argument (JOCKY-E2004)
        if actual_arg_count < spec.min_args:
            call_signature = f"{namespace}.{function}({', '.join(a.name for a in spec.arguments)})"
            self.reporter.error(
                code=DiagnosticCode.MISSING_ARGUMENT,
                message=f"Function '{namespace}.{function}' expects {spec.min_args} argument{'s' if spec.min_args != 1 else ''}.",
                line=call.line,
                column=call.column,
                offset=call.offset,
                length=len(namespace) + 1 + len(function),
                help_text=f"Expected:\n{call_signature}",
            )
            return

        # 4. Wrong Argument Count / Excess Arguments (JOCKY-E2003)
        if actual_arg_count > spec.max_args:
            arg_str = "argument" if actual_arg_count == 1 else "arguments"
            was_str = "was" if actual_arg_count == 1 else "were"
            self.reporter.error(
                code=DiagnosticCode.WRONG_ARGUMENT_COUNT,
                message=f"Function '{namespace}.{function}' expects {spec.max_args} arguments, but {actual_arg_count} {arg_str} {was_str} provided.",
                line=call.line,
                column=call.column,
                offset=call.offset,
                length=len(namespace) + 1 + len(function),
                help_text=f"Expected:\n{namespace}.{function}({', '.join(a.name for a in spec.arguments)})",
            )
            return

        # 5. Validate Argument Types (JOCKY-E2005)
        for idx, (arg_node, expected_arg_spec) in enumerate(zip(call.arguments, spec.arguments), start=1):
            if arg_node.arg_type == "identifier":
                resolved = scope.get(str(arg_node.value))
                if resolved is None:
                    self.reporter.error(
                        code=DiagnosticCode.UNKNOWN_IDENTIFIER,
                        message=f"Unknown variable '{arg_node.value}'.",
                        line=arg_node.line,
                        column=arg_node.column,
                        offset=arg_node.offset,
                        length=len(str(arg_node.value)),
                        help_text="Define the variable with `let` before using it as an argument.",
                    )
                    continue
                arg_node.resolved_value, arg_node.resolved_type = resolved
                actual_type = arg_node.resolved_type
            else:
                actual_type = arg_node.arg_type
            if actual_type != expected_arg_spec.type:
                self.reporter.error(
                    code=DiagnosticCode.WRONG_ARGUMENT_TYPE,
                    message=f"Invalid argument type for '{namespace}.{function}'.",
                    line=arg_node.line,
                    column=arg_node.column,
                    offset=arg_node.offset,
                    length=len(str(arg_node.value)),
                    help_text=f"Expected:\n{expected_arg_spec.type}\n\nReceived:\n{actual_type}",
                )

    def _resolve_expression(self, expression: Any, scope: Dict[str, Tuple[Any, str]]) -> Optional[Tuple[Any, str]]:
        if isinstance(expression, Identifier):
            resolved = scope.get(expression.name)
            if resolved is None:
                self.reporter.error(
                    code=DiagnosticCode.UNKNOWN_IDENTIFIER,
                    message=f"Unknown variable '{expression.name}'.",
                    line=expression.line,
                    column=expression.column,
                    offset=expression.offset,
                    length=len(expression.name),
                    help_text="Define the variable with `let` before using it.",
                )
            return resolved
        if isinstance(expression, BinaryOperation):
            left = self._resolve_expression(expression.left, scope)
            right = self._resolve_expression(expression.right, scope)
            if left is None or right is None:
                return None
            if expression.op in ("&&", "||"):
                return (bool(left[0]) and bool(right[0]), "boolean") if expression.op == "&&" else (bool(left[0]) or bool(right[0]), "boolean")
            return None
        if isinstance(expression, bool):
            return expression, "boolean"
        if hasattr(expression, "value"):
            value = expression.value
            return value, "number" if isinstance(value, (int, float)) else "string"
        return None
