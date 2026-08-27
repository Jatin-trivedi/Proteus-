from dataclasses import dataclass
from typing import List, Optional, Any

@dataclass
class ASTNode:
    pass

@dataclass
class Program(ASTNode):
    body: List[ASTNode]

@dataclass
class AgentDeclaration(ASTNode):
    name: str
    body: List[ASTNode]

@dataclass
class LetStatement(ASTNode):
    name: str
    value: ASTNode

@dataclass
class ReturnStatement(ASTNode):
    value: ASTNode

@dataclass
class CallExpression(ASTNode):
    function: str
    arguments: List[ASTNode]

@dataclass
class StringLiteral(ASTNode):
    value: str

@dataclass
class NumberLiteral(ASTNode):
    value: float

@dataclass
class Identifier(ASTNode):
    value: str

@dataclass
class BinaryOperation(ASTNode):
    left: ASTNode
    operator: str
    right: ASTNode

@dataclass
class IfStatement(ASTNode):
    condition: ASTNode
    then_body: List[ASTNode]
    else_body: List[ASTNode]

@dataclass
class WhileStatement(ASTNode):
    condition: ASTNode
    body: List[ASTNode]

@dataclass
class ForStatement(ASTNode):
    var: str
    start: ASTNode
    end: ASTNode
    body: List[ASTNode]

@dataclass
class ArrayLiteral(ASTNode):
    elements: List[ASTNode]

@dataclass
class ArrayIndex(ASTNode):
    array: ASTNode   # Identifier
    index: ASTNode

@dataclass
class StructLiteral(ASTNode):
    fields: List['StructField']

@dataclass
class StructField(ASTNode):
    name: str
    value: ASTNode

@dataclass
class StructDeclaration(ASTNode):
    name: str
    fields: List[str]

@dataclass
class FunctionDeclaration(ASTNode):
    name: str
    params: List[str]
    body: List[ASTNode]

# NEW: for field access like p.name
@dataclass
class StructFieldAccess(ASTNode):
    object: ASTNode   # Identifier
    field: str