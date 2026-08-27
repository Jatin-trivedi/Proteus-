from .tokens import Token, TokenType

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        
        self.keywords = {
            'agent': TokenType.AGENT,
            'let': TokenType.LET,
            'return': TokenType.RETURN,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'while': TokenType.WHILE,
            'for': TokenType.FOR,
            'in': TokenType.IN,
            'to': TokenType.TO,
            'true': TokenType.TRUE,
            'false': TokenType.FALSE,
            'null': TokenType.NULL,
            'function': TokenType.FUNCTION,
            'struct': TokenType.STRUCT,      # <-- ADDED
        }
        
        self.single_char = {
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
            ';': TokenType.SEMICOLON,
            ',': TokenType.COMMA,
            '.': TokenType.DOT,
            ':': TokenType.COLON,
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.MULTIPLY,
            '/': TokenType.DIVIDE,
            '=': TokenType.ASSIGN,
            '<': TokenType.LESS_THAN,
            '>': TokenType.GREATER_THAN,
        }
    
    def tokenize(self):
        while self.position < len(self.source):
            char = self.source[self.position]
            
            if char.isspace():
                if char == '\n':
                    self.line += 1
                    self.column = 1
                else:
                    self.column += 1
                self.position += 1
                continue
            
            if char == '#':
                while self.position < len(self.source) and self.source[self.position] != '\n':
                    self.position += 1
                continue
            
            if char == '"':
                self._read_string()
                continue
            
            if char.isdigit():
                self._read_number()
                continue
            
            if char.isalpha() or char == '_':
                self._read_identifier()
                continue
            
            if char == '=' and self._peek() == '=':
                self.tokens.append(Token(TokenType.EQUALS, '==', self.line, self.column))
                self.position += 2
                self.column += 2
                continue
            
            if char == '!' and self._peek() == '=':
                self.tokens.append(Token(TokenType.NOT_EQUALS, '!=', self.line, self.column))
                self.position += 2
                self.column += 2
                continue
            
            if char in self.single_char:
                self.tokens.append(Token(self.single_char[char], char, self.line, self.column))
                self.position += 1
                self.column += 1
                continue
            
            raise SyntaxError(f"Unknown character '{char}' at line {self.line}, column {self.column}")
        
        self.tokens.append(Token(TokenType.EOF, 'EOF', self.line, self.column))
        return self.tokens
    
    def _read_string(self):
        start_line = self.line
        start_col = self.column
        self.position += 1
        self.column += 1
        value = ''
        
        while self.position < len(self.source):
            char = self.source[self.position]
            if char == '"':
                self.position += 1
                self.column += 1
                self.tokens.append(Token(TokenType.STRING, value, start_line, start_col))
                return
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            value += char
            self.position += 1
        
        raise SyntaxError(f"Unterminated string at line {start_line}, column {start_col}")
    
    def _read_number(self):
        start_line = self.line
        start_col = self.column
        value = ''
        
        while self.position < len(self.source) and (self.source[self.position].isdigit() or self.source[self.position] == '.'):
            value += self.source[self.position]
            self.position += 1
            self.column += 1
        
        self.tokens.append(Token(TokenType.NUMBER, value, start_line, start_col))
    
    def _read_identifier(self):
        start_line = self.line
        start_col = self.column
        value = ''
        
        while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == '_'):
            value += self.source[self.position]
            self.position += 1
            self.column += 1
        
        token_type = self.keywords.get(value, TokenType.IDENTIFIER)
        self.tokens.append(Token(token_type, value, start_line, start_col))
    
    def _peek(self):
        if self.position + 1 < len(self.source):
            return self.source[self.position + 1]
        return ''