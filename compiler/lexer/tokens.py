from enum import Enum, auto
from typing import Any, Optional


class TokenType(Enum):
    # Literals & Identifiers
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()

    # Keywords
    ANALYSIS = auto()
    AGENT = auto()
    FUNCTION = auto()
    STRUCT = auto()
    LET = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    TO = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    PRINT = auto()

    # Operators
    ASSIGN = auto()
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS_THAN = auto()
    GREATER_THAN = auto()
    DOT = auto()
    COLON = auto()
    COMMA = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMICOLON = auto()

    # End of File
    EOF = auto()


class Token:
    def __init__(
        self,
        type: TokenType,
        value: Any,
        line: int = 1,
        column: int = 1,
        offset: int = 0,
        length: Optional[int] = None,
    ):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
        self.offset = offset
        self.length = length if length is not None else (len(str(value)) if value is not None else 0)

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column}, off={self.offset})"

    def to_dict(self):
        return {
            "type": self.type.name,
            "value": self.value,
            "line": self.line,
            "column": self.column,
            "offset": self.offset,
            "length": self.length,
        }