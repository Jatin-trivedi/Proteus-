from enum import Enum, auto

class TokenType(Enum):
    # Keywords
    AGENT = auto()
    LET = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    
    # Identifiers & Literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    
    # Operators
    ASSIGN = auto()      # =
    EQUALS = auto()      # ==
    NOT_EQUALS = auto()  # !=
    LESS_THAN = auto()   # <
    GREATER_THAN = auto() # >
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    
    # Delimiters
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    LBRACE = auto()      # {
    RBRACE = auto()      # }
    SEMICOLON = auto()   # ;
    COMMA = auto()       # ,
    DOT = auto()         # .
    COLON = auto()       # :
    
    # Special
    EOF = auto()
    COMMENT = auto()

class Token:
    def __init__(self, type: TokenType, value: str, line: int, column: int):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
    
    def __repr__(self):
        return f"Token({self.type}, '{self.value}', line={self.line}, col={self.column})"