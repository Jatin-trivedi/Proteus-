from typing import List, Optional
from .tokens import Token, TokenType

try:
    from compiler.diagnostics.diagnostics import DiagnosticReporter, DiagnosticCode
except (ImportError, ModuleNotFoundError):
    from diagnostics.diagnostics import DiagnosticReporter, DiagnosticCode


class Lexer:
    def __init__(self, source: str, filename: str = "<input>", reporter: Optional[DiagnosticReporter] = None):
        self.source = source
        self.filename = filename
        self.reporter = reporter or DiagnosticReporter(source, filename)
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

        self.keywords = {
            "analysis": TokenType.ANALYSIS,
            "agent": TokenType.AGENT,
            "let": TokenType.LET,
            "return": TokenType.RETURN,
            "if": TokenType.IF,
            "else": TokenType.ELSE,
            "while": TokenType.WHILE,
            "for": TokenType.FOR,
            "in": TokenType.IN,
            "to": TokenType.TO,
            "true": TokenType.BOOLEAN,
            "false": TokenType.BOOLEAN,
            "null": TokenType.NULL,
            "function": TokenType.FUNCTION,
            "struct": TokenType.STRUCT,
            "print": TokenType.PRINT,
        }

        self.single_char = {
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            ";": TokenType.SEMICOLON,
            ",": TokenType.COMMA,
            ".": TokenType.DOT,
            ":": TokenType.COLON,
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.MULTIPLY,
            "/": TokenType.DIVIDE,
            "=": TokenType.ASSIGN,
            "<": TokenType.LESS_THAN,
            ">": TokenType.GREATER_THAN,
        }

    def tokenize(self) -> List[Token]:
        while self.position < len(self.source):
            char = self.source[self.position]

            if char.isspace():
                if char == "\n":
                    self.line += 1
                    self.column = 1
                else:
                    self.column += 1
                self.position += 1
                continue

            # Comments: # or //
            if char == "#" or (char == "/" and self._peek() == "/"):
                while self.position < len(self.source) and self.source[self.position] != "\n":
                    self.position += 1
                continue

            if char == '"':
                self._read_string()
                continue

            if char.isdigit():
                self._read_number()
                continue

            if char.isalpha() or char == "_":
                self._read_identifier()
                continue

            if char == "=" and self._peek() == "=":
                start_line = self.line
                start_col = self.column
                start_pos = self.position
                self.position += 2
                self.column += 2
                self.tokens.append(Token(TokenType.EQUALS, "==", start_line, start_col, start_pos, 2))
                continue

            if char == "!" and self._peek() == "=":
                start_line = self.line
                start_col = self.column
                start_pos = self.position
                self.position += 2
                self.column += 2
                self.tokens.append(Token(TokenType.NOT_EQUALS, "!=", start_line, start_col, start_pos, 2))
                continue

            if char == "&" and self._peek() == "&":
                start_line = self.line
                start_col = self.column
                start_pos = self.position
                self.position += 2
                self.column += 2
                self.tokens.append(Token(TokenType.AND, "&&", start_line, start_col, start_pos, 2))
                continue

            if char == "|" and self._peek() == "|":
                start_line = self.line
                start_col = self.column
                start_pos = self.position
                self.position += 2
                self.column += 2
                self.tokens.append(Token(TokenType.OR, "||", start_line, start_col, start_pos, 2))
                continue

            if char in self.single_char:
                start_line = self.line
                start_col = self.column
                start_pos = self.position
                self.position += 1
                self.column += 1
                self.tokens.append(Token(self.single_char[char], char, start_line, start_col, start_pos, 1))
                continue

            # Unknown character
            err_line = self.line
            err_col = self.column
            err_pos = self.position
            self.reporter.error(
                code=DiagnosticCode.UNEXPECTED_CHARACTER,
                message=f"Unexpected character '{char}'",
                line=err_line,
                column=err_col,
                offset=err_pos,
                length=1,
            )
            self.position += 1
            self.column += 1

        self.tokens.append(Token(TokenType.EOF, "EOF", self.line, self.column, self.position, 0))
        return self.tokens

    def _read_string(self):
        start_line = self.line
        start_col = self.column
        start_pos = self.position
        self.position += 1
        self.column += 1
        value = ""

        while self.position < len(self.source):
            char = self.source[self.position]
            if char == '"':
                self.position += 1
                self.column += 1
                length = self.position - start_pos
                self.tokens.append(Token(TokenType.STRING, value, start_line, start_col, start_pos, length))
                return
            if char == "\\":
                next_char = self.source[self.position + 1] if self.position + 1 < len(self.source) else ""
                if next_char == "n":
                    value += "\n"
                elif next_char == "t":
                    value += "\t"
                elif next_char == "r":
                    value += "\r"
                elif next_char == '"':
                    value += '"'
                elif next_char == "\\":
                    value += "\\"
                else:
                    value += next_char
                self.position += 2
                self.column += 2
                continue
            if char == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            value += char
            self.position += 1

        length = self.position - start_pos
        self.reporter.error(
            code=DiagnosticCode.UNTERMINATED_STRING,
            message=f"Unterminated string starting at line {start_line}, column {start_col}",
            line=start_line,
            column=start_col,
            offset=start_pos,
            length=length,
            help_text='Add a closing double-quote `"` to terminate the string literal.',
        )

    def _read_number(self):
        start_line = self.line
        start_col = self.column
        start_pos = self.position
        value = ""

        while self.position < len(self.source) and (self.source[self.position].isdigit() or self.source[self.position] == "."):
            if self.source[self.position] == ".":
                if self.position + 1 < len(self.source) and self.source[self.position + 1].isdigit():
                    value += self.source[self.position]
                    self.position += 1
                    self.column += 1
                else:
                    break
            else:
                value += self.source[self.position]
                self.position += 1
                self.column += 1

        length = len(value)
        num_val: int | float
        if "." in value:
            try:
                num_val = float(value)
            except ValueError:
                num_val = 0.0
                self.reporter.error(
                    code=DiagnosticCode.INVALID_NUMBER,
                    message=f"Invalid floating point number '{value}'",
                    line=start_line,
                    column=start_col,
                    offset=start_pos,
                    length=length,
                )
        else:
            try:
                num_val = int(value)
            except ValueError:
                num_val = 0
                self.reporter.error(
                    code=DiagnosticCode.INVALID_NUMBER,
                    message=f"Invalid integer number '{value}'",
                    line=start_line,
                    column=start_col,
                    offset=start_pos,
                    length=length,
                )

        self.tokens.append(Token(TokenType.NUMBER, num_val, start_line, start_col, start_pos, length))

    def _read_identifier(self):
        start_line = self.line
        start_col = self.column
        start_pos = self.position
        value = ""

        while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == "_"):
            value += self.source[self.position]
            self.position += 1
            self.column += 1

        token_type = self.keywords.get(value, TokenType.IDENTIFIER)
        length = len(value)
        if token_type == TokenType.BOOLEAN:
            bool_val = (value == "true")
            self.tokens.append(Token(token_type, bool_val, start_line, start_col, start_pos, length))
        else:
            self.tokens.append(Token(token_type, value, start_line, start_col, start_pos, length))

    def _peek(self) -> str:
        if self.position + 1 < len(self.source):
            return self.source[self.position + 1]
        return ""