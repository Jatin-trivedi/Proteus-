from lexer.tokens import TokenType
from syntax.nodes import *

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.current_token = self.tokens[0] if tokens else None
    
    def parse(self):
        statements = []
        
        while self.current_token and self.current_token.type != TokenType.EOF:
            if self.current_token.type == TokenType.AGENT:
                statements.append(self._parse_agent())
            else:
                raise SyntaxError(f"Unexpected token '{self.current_token.value}' at line {self.current_token.line}")
        
        return Program(statements)
    
    def _parse_agent(self):
        self._consume(TokenType.AGENT)
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.LBRACE)
        
        body = []
        while self.current_token.type != TokenType.RBRACE:
            if self.current_token.type == TokenType.LET:
                body.append(self._parse_let())
            elif self.current_token.type == TokenType.RETURN:
                body.append(self._parse_return())
            else:
                raise SyntaxError(f"Unexpected token '{self.current_token.value}' in agent body")
        
        self._consume(TokenType.RBRACE)
        return AgentDeclaration(name, body)
    
    def _parse_let(self):
        self._consume(TokenType.LET)
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.ASSIGN)
        value = self._parse_expression()
        return LetStatement(name, value)
    
    def _parse_return(self):
        self._consume(TokenType.RETURN)
        value = self._parse_expression()
        return ReturnStatement(value)
    
    def _parse_expression(self):
        return self._parse_binary_expression()
    
    def _parse_binary_expression(self, min_precedence=0):
        left = self._parse_primary()
        
        while True:
            token = self.current_token
            if token.type not in [TokenType.EQUALS, TokenType.NOT_EQUALS, 
                                  TokenType.LESS_THAN, TokenType.GREATER_THAN,
                                  TokenType.PLUS, TokenType.MINUS,
                                  TokenType.MULTIPLY, TokenType.DIVIDE]:
                break
            
            precedence = self._get_precedence(token.type)
            if precedence < min_precedence:
                break
            
            self._advance()
            right = self._parse_binary_expression(precedence + 1)
            left = BinaryOperation(left, token.value, right)
        
        return left
    
    def _parse_primary(self):
        token = self.current_token
        
        if token.type == TokenType.STRING:
            self._advance()
            return StringLiteral(token.value)
        
        if token.type == TokenType.NUMBER:
            self._advance()
            return NumberLiteral(float(token.value))
        
        if token.type == TokenType.IDENTIFIER:
            self._advance()
            if self.current_token and self.current_token.type == TokenType.LPAREN:
                return self._parse_call(token.value)
            return Identifier(token.value)
        
        if token.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN)
            return expr
        
        raise SyntaxError(f"Unexpected token '{token.value}' in expression")
    
    def _parse_call(self, function_name):
        self._consume(TokenType.LPAREN)
        args = []
        
        while self.current_token.type != TokenType.RPAREN:
            args.append(self._parse_expression())
            if self.current_token.type == TokenType.COMMA:
                self._advance()
                continue
            break
        
        self._consume(TokenType.RPAREN)
        return CallExpression(function_name, args)
    
    def _consume(self, expected_type):
        if self.current_token.type != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {self.current_token.type}")
        token = self.current_token
        self._advance()
        return token
    
    def _advance(self):
        self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = None
    
    def _get_precedence(self, token_type):
        precedence = {
            TokenType.MULTIPLY: 3,
            TokenType.DIVIDE: 3,
            TokenType.PLUS: 2,
            TokenType.MINUS: 2,
            TokenType.EQUALS: 1,
            TokenType.NOT_EQUALS: 1,
            TokenType.LESS_THAN: 1,
            TokenType.GREATER_THAN: 1,
        }
        return precedence.get(token_type, 0)
