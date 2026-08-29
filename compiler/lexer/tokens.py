from enum import Enum, auto

class TokenType(Enum):
    # Literals & Identifiers
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    PRINT = auto()

    # Keywords
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
    def __init__(self, type: TokenType, value, line=None, column=None):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r})"