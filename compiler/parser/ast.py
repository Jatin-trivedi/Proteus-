import json
from typing import Any, List, Optional


class ASTNode:
    def __init__(self, line: int = 1, column: int = 1, offset: int = 0):
        self.line = line
        self.column = column
        self.offset = offset

    def to_dict(self) -> dict:
        return {"type": self.__class__.__name__}

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_dict()})"


class Argument(ASTNode):
    def __init__(
        self,
        value: Any,
        arg_type: str,
        line: int = 1,
        column: int = 1,
        offset: int = 0,
    ):
        super().__init__(line, column, offset)
        self.value = value
        self.arg_type = arg_type  # 'string', 'number', 'boolean'

    def to_dict(self) -> dict:
        return {
            "type": "Argument",
            "arg_type": self.arg_type,
            "value": self.value,
        }


class FunctionCall(ASTNode):
    def __init__(
        self,
        namespace: str,
        function: str,
        arguments: Optional[List[Argument]] = None,
        line: int = 1,
        column: int = 1,
        offset: int = 0,
    ):
        super().__init__(line, column, offset)
        self.namespace = namespace
        self.function = function
        self.arguments = arguments if arguments is not None else []

    def to_dict(self) -> dict:
        return {
            "type": "FunctionCall",
            "namespace": self.namespace,
            "function": self.function,
            "arguments": [arg.to_dict() for arg in self.arguments],
        }


class AnalysisBlock(ASTNode):
    def __init__(
        self,
        name: str,
        statements: Optional[List[FunctionCall]] = None,
        line: int = 1,
        column: int = 1,
        offset: int = 0,
    ):
        super().__init__(line, column, offset)
        self.name = name
        self.statements = statements if statements is not None else []
        self.body = self.statements  # alias for legacy compatibility

    def to_dict(self) -> dict:
        return {
            "type": "AnalysisBlock",
            "name": self.name,
            "statements": [stmt.to_dict() for stmt in self.statements],
        }


# Alias for backward compatibility
AnalysisDeclaration = AnalysisBlock


class Program(ASTNode):
    def __init__(
        self,
        body: Optional[List[ASTNode]] = None,
        line: int = 1,
        column: int = 1,
        offset: int = 0,
    ):
        super().__init__(line, column, offset)
        self.body = body if body is not None else []
        self.declarations = self.body

    @property
    def analyses(self) -> List[AnalysisBlock]:
        return [decl for decl in self.body if isinstance(decl, AnalysisBlock)]

    def to_dict(self) -> dict:
        analyses_list = [decl.to_dict() for decl in self.analyses]
        if analyses_list:
            return {
                "type": "Program",
                "analyses": analyses_list,
            }
        return {
            "type": "Program",
            "body": [node.to_dict() for node in self.body],
        }


# ==============================================================================
# Legacy AST nodes preserved for backward compatibility
# ==============================================================================

class AgentDeclaration(ASTNode):
    def __init__(self, name, body, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.name = name
        self.body = body

    def to_dict(self) -> dict:
        return {
            "type": "AgentDeclaration",
            "name": self.name,
            "body": [b.to_dict() if hasattr(b, "to_dict") else str(b) for b in self.body],
        }


class FunctionDeclaration(ASTNode):
    def __init__(self, name, params, body, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.name = name
        self.params = params
        self.body = body

    def to_dict(self) -> dict:
        return {
            "type": "FunctionDeclaration",
            "name": self.name,
            "params": self.params,
            "body": [b.to_dict() if hasattr(b, "to_dict") else str(b) for b in self.body],
        }


class StructDeclaration(ASTNode):
    def __init__(self, name, fields, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.name = name
        self.fields = fields

    def to_dict(self) -> dict:
        return {
            "type": "StructDeclaration",
            "name": self.name,
            "fields": self.fields,
        }


class LetStatement(ASTNode):
    def __init__(self, name, value, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.name = name
        self.value = value

    def to_dict(self) -> dict:
        return {
            "type": "LetStatement",
            "name": self.name,
            "value": self.value.to_dict() if hasattr(self.value, "to_dict") else self.value,
        }


class ReturnStatement(ASTNode):
    def __init__(self, value, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.value = value

    def to_dict(self) -> dict:
        return {
            "type": "ReturnStatement",
            "value": self.value.to_dict() if hasattr(self.value, "to_dict") else self.value,
        }


class PrintStatement(ASTNode):
    def __init__(self, args, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.args = args

    def to_dict(self) -> dict:
        return {
            "type": "PrintStatement",
            "args": [a.to_dict() if hasattr(a, "to_dict") else a for a in self.args],
        }


class IfStatement(ASTNode):
    def __init__(self, cond, then_body, else_body, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body

    def to_dict(self) -> dict:
        return {
            "type": "IfStatement",
            "cond": self.cond.to_dict() if hasattr(self.cond, "to_dict") else self.cond,
            "then_body": [b.to_dict() if hasattr(b, "to_dict") else str(b) for b in self.then_body],
            "else_body": [b.to_dict() if hasattr(b, "to_dict") else str(b) for b in self.else_body] if self.else_body else [],
        }


class WhileStatement(ASTNode):
    def __init__(self, cond, body, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.cond = cond
        self.body = body

    def to_dict(self) -> dict:
        return {
            "type": "WhileStatement",
            "cond": self.cond.to_dict() if hasattr(self.cond, "to_dict") else self.cond,
            "body": [b.to_dict() if hasattr(b, "to_dict") else str(b) for b in self.body],
        }


class ForStatement(ASTNode):
    def __init__(self, var, start, end, body, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.var = var
        self.start = start
        self.end = end
        self.body = body

    def to_dict(self) -> dict:
        return {
            "type": "ForStatement",
            "var": self.var,
            "start": self.start.to_dict() if hasattr(self.start, "to_dict") else self.start,
            "end": self.end.to_dict() if hasattr(self.end, "to_dict") else self.end,
            "body": [b.to_dict() if hasattr(b, "to_dict") else str(b) for b in self.body],
        }


class BinaryOperation(ASTNode):
    def __init__(self, left, op, right, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.left = left
        self.op = op
        self.right = right

    def to_dict(self) -> dict:
        return {
            "type": "BinaryOperation",
            "left": self.left.to_dict() if hasattr(self.left, "to_dict") else self.left,
            "op": self.op,
            "right": self.right.to_dict() if hasattr(self.right, "to_dict") else self.right,
        }


class StringLiteral(ASTNode):
    def __init__(self, value, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.value = value

    def to_dict(self) -> dict:
        return {"type": "StringLiteral", "value": self.value}


class NumberLiteral(ASTNode):
    def __init__(self, value, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.value = value

    def to_dict(self) -> dict:
        return {"type": "NumberLiteral", "value": self.value}


class Identifier(ASTNode):
    def __init__(self, name, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.name = name

    def to_dict(self) -> dict:
        return {"type": "Identifier", "name": self.name}


class ArrayIndex(ASTNode):
    def __init__(self, array, index, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.array = array
        self.index = index


class StructLiteral(ASTNode):
    def __init__(self, fields, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.fields = fields


class StructField(ASTNode):
    def __init__(self, name, value, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.name = name
        self.value = value


class StructFieldAccess(ASTNode):
    def __init__(self, struct, field_name, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.struct = struct
        self.field_name = field_name


class ArrayLiteral(ASTNode):
    def __init__(self, elements, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.elements = elements


class CallExpression(ASTNode):
    def __init__(self, name, args, line=1, column=1, offset=0):
        super().__init__(line, column, offset)
        self.name = name
        self.args = args
