from dataclasses import dataclass
from typing import List, Optional, Any

@dataclass
class ASTNode:
    pass

@dataclass
class Program(ASTNode):
    """Root node containing all statements"""
    body: List[ASTNode]

@dataclass
class AgentDeclaration(ASTNode):
    """agent <name> { <statements> }"""
    name: str
    body: List[ASTNode]

@dataclass
class LetStatement(ASTNode):
    """let <identifier> = <expression>"""
    name: str
    value: ASTNode

@dataclass
class ReturnStatement(ASTNode):
    """return <expression>"""
    value: ASTNode

@dataclass
class CallExpression(ASTNode):
    """<function>(<arguments>)"""
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