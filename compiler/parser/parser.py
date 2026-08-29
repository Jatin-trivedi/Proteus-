from lexer.tokens import TokenType
from syntax.nodes import *  # Ensure PrintStatement is in syntax.nodes

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
            elif self.current_token.type == TokenType.FUNCTION:
                statements.append(self._parse_function_declaration())
            elif self.current_token.type == TokenType.STRUCT:
                statements.append(self._parse_struct_declaration())
            else:
                raise SyntaxError(f"Unexpected token '{self.current_token.value}'")
        return Program(statements)

    # *** THIS IS THE METHOD YOU ARE MISSING ***
    def _parse_agent(self):
        self._consume(TokenType.AGENT)
        name = self._consume(TokenType.IDENTIFIER).value

        if self.current_token and self.current_token.type == TokenType.ASSIGN:
            self._advance()

        self._consume(TokenType.LBRACE)
        body = []
        while self.current_token.type != TokenType.RBRACE:
            if self.current_token.type == TokenType.LET:
                body.append(self._parse_let())
            elif self.current_token.type == TokenType.RETURN:
                body.append(self._parse_return())
            elif self.current_token.type == TokenType.IF:
                body.append(self._parse_if())
            elif self.current_token.type == TokenType.WHILE:
                body.append(self._parse_while())
            elif self.current_token.type == TokenType.FOR:
                body.append(self._parse_for())
            elif self.current_token.type == TokenType.PRINT:
                body.append(self._parse_print())
            elif self.current_token.type == TokenType.IDENTIFIER:
                # Check if it's a function call like run(...) or an assignment like x = ...
                if self._peek_token() and self._peek_token().type == TokenType.LPAREN:
                    call_expr = self._parse_call(self._consume(TokenType.IDENTIFIER).value)
                    self._consume_semicolon()
                    body.append(call_expr)
                else:
                    name_var = self._consume(TokenType.IDENTIFIER).value
                    self._consume(TokenType.ASSIGN)
                    value = self._parse_expression()
                    self._consume_semicolon()
                    body.append(LetStatement(name_var, value))
            else:
                raise SyntaxError(f"Unexpected token '{self.current_token.value}' in agent body")
        self._consume(TokenType.RBRACE)
        return AgentDeclaration(name, body)

    def _parse_function_declaration(self):
        self._consume(TokenType.FUNCTION)
        func_name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.LPAREN)
        params = []
        while self.current_token.type != TokenType.RPAREN:
            params.append(self._consume(TokenType.IDENTIFIER).value)
            if self.current_token.type == TokenType.COMMA:
                self._advance()
        self._consume(TokenType.RPAREN)
        self._consume(TokenType.LBRACE)
        body = []
        while self.current_token.type != TokenType.RBRACE:
            if self.current_token.type == TokenType.LET:
                body.append(self._parse_let())
            elif self.current_token.type == TokenType.RETURN:
                body.append(self._parse_return())
            elif self.current_token.type == TokenType.IF:
                body.append(self._parse_if())
            elif self.current_token.type == TokenType.WHILE:
                body.append(self._parse_while())
            elif self.current_token.type == TokenType.FOR:
                body.append(self._parse_for())
            elif self.current_token.type == TokenType.PRINT:
                body.append(self._parse_print())
            elif self.current_token.type == TokenType.IDENTIFIER:
                # Check if it's a function call
                if self._peek_token() and self._peek_token().type == TokenType.LPAREN:
                    call_expr = self._parse_call(self._consume(TokenType.IDENTIFIER).value)
                    self._consume_semicolon()
                    body.append(call_expr)
                else:
                    name_var = self._consume(TokenType.IDENTIFIER).value
                    self._consume(TokenType.ASSIGN)
                    value = self._parse_expression()
                    self._consume_semicolon()
                    body.append(LetStatement(name_var, value))
            else:
                raise SyntaxError("Unexpected token in function body")
        self._consume(TokenType.RBRACE)
        return FunctionDeclaration(func_name, params, body)

    def _parse_struct_declaration(self):
        self._consume(TokenType.STRUCT)
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.LBRACE)
        fields = []
        while self.current_token.type != TokenType.RBRACE:
            fields.append(self._consume(TokenType.IDENTIFIER).value)
            if self.current_token.type == TokenType.COMMA:
                self._advance()
        self._consume(TokenType.RBRACE)
        return StructDeclaration(name, fields)

    def _parse_if(self):
        self._consume(TokenType.IF)
        self._consume(TokenType.LPAREN)
        cond = self._parse_expression()
        self._consume(TokenType.RPAREN)
        self._consume(TokenType.LBRACE)
        then_body = []
        while self.current_token.type != TokenType.RBRACE:
            if self.current_token.type == TokenType.LET:
                then_body.append(self._parse_let())
            elif self.current_token.type == TokenType.RETURN:
                then_body.append(self._parse_return())
            elif self.current_token.type == TokenType.IF:
                then_body.append(self._parse_if())
            elif self.current_token.type == TokenType.WHILE:
                then_body.append(self._parse_while())
            elif self.current_token.type == TokenType.PRINT:
                then_body.append(self._parse_print())
            elif self.current_token.type == TokenType.IDENTIFIER:
                # Check if it's a function call
                if self._peek_token() and self._peek_token().type == TokenType.LPAREN:
                    call_expr = self._parse_call(self._consume(TokenType.IDENTIFIER).value)
                    self._consume_semicolon()
                    then_body.append(call_expr)
                else:
                    name_var = self._consume(TokenType.IDENTIFIER).value
                    self._consume(TokenType.ASSIGN)
                    value = self._parse_expression()
                    self._consume_semicolon()
                    then_body.append(LetStatement(name_var, value))
            else:
                raise SyntaxError("Unexpected token in if body")
        self._consume(TokenType.RBRACE)
        else_body = []
        if self.current_token.type == TokenType.ELSE:
            self._advance()
            self._consume(TokenType.LBRACE)
            while self.current_token.type != TokenType.RBRACE:
                if self.current_token.type == TokenType.LET:
                    else_body.append(self._parse_let())
                elif self.current_token.type == TokenType.RETURN:
                    else_body.append(self._parse_return())
                elif self.current_token.type == TokenType.IF:
                    else_body.append(self._parse_if())
                elif self.current_token.type == TokenType.PRINT:
                    else_body.append(self._parse_print())
                elif self.current_token.type == TokenType.IDENTIFIER:
                    # Check if it's a function call
                    if self._peek_token() and self._peek_token().type == TokenType.LPAREN:
                        call_expr = self._parse_call(self._consume(TokenType.IDENTIFIER).value)
                        self._consume_semicolon()
                        else_body.append(call_expr)
                    else:
                        name_var = self._consume(TokenType.IDENTIFIER).value
                        self._consume(TokenType.ASSIGN)
                        value = self._parse_expression()
                        self._consume_semicolon()
                        else_body.append(LetStatement(name_var, value))
                else:
                    raise SyntaxError("Unexpected token in else body")
            self._consume(TokenType.RBRACE)
        return IfStatement(cond, then_body, else_body)

    def _parse_while(self):
        self._consume(TokenType.WHILE)
        self._consume(TokenType.LPAREN)
        cond = self._parse_expression()
        self._consume(TokenType.RPAREN)
        self._consume(TokenType.LBRACE)
        body = []
        while self.current_token.type != TokenType.RBRACE:
            if self.current_token.type == TokenType.LET:
                body.append(self._parse_let())
            elif self.current_token.type == TokenType.RETURN:
                body.append(self._parse_return())
            elif self.current_token.type == TokenType.PRINT:
                body.append(self._parse_print())
            elif self.current_token.type == TokenType.IDENTIFIER:
                # Check if it's a function call
                if self._peek_token() and self._peek_token().type == TokenType.LPAREN:
                    call_expr = self._parse_call(self._consume(TokenType.IDENTIFIER).value)
                    self._consume_semicolon()
                    body.append(call_expr)
                else:
                    name_var = self._consume(TokenType.IDENTIFIER).value
                    self._consume(TokenType.ASSIGN)
                    value = self._parse_expression()
                    self._consume_semicolon()
                    body.append(LetStatement(name_var, value))
            elif self.current_token.type == TokenType.IF:
                body.append(self._parse_if())
            elif self.current_token.type == TokenType.WHILE:
                body.append(self._parse_while())
            else:
                raise SyntaxError(f"Unexpected token '{self.current_token.value}' in while body")
        self._consume(TokenType.RBRACE)
        return WhileStatement(cond, body)

    def _parse_for(self):
        self._consume(TokenType.FOR)
        var = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.IN)
        start = self._parse_expression()
        self._consume(TokenType.TO)
        end = self._parse_expression()
        self._consume(TokenType.LBRACE)
        body = []
        while self.current_token.type != TokenType.RBRACE:
            if self.current_token.type == TokenType.LET:
                body.append(self._parse_let())
            elif self.current_token.type == TokenType.RETURN:
                body.append(self._parse_return())
            elif self.current_token.type == TokenType.IF:
                body.append(self._parse_if())
            elif self.current_token.type == TokenType.WHILE:
                body.append(self._parse_while())
            elif self.current_token.type == TokenType.PRINT:
                body.append(self._parse_print())
            elif self.current_token.type == TokenType.IDENTIFIER:
                # Check if it's a function call
                if self._peek_token() and self._peek_token().type == TokenType.LPAREN:
                    call_expr = self._parse_call(self._consume(TokenType.IDENTIFIER).value)
                    self._consume_semicolon()
                    body.append(call_expr)
                else:
                    name_var = self._consume(TokenType.IDENTIFIER).value
                    self._consume(TokenType.ASSIGN)
                    value = self._parse_expression()
                    self._consume_semicolon()
                    body.append(LetStatement(name_var, value))
            else:
                raise SyntaxError("Unexpected token in for body")
        self._consume(TokenType.RBRACE)
        return ForStatement(var, start, end, body)

    def _parse_let(self):
        self._consume(TokenType.LET)
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.ASSIGN)
        value = self._parse_expression()
        self._consume_semicolon()
        return LetStatement(name, value)

    def _parse_return(self):
        self._consume(TokenType.RETURN)
        value = self._parse_expression()
        self._consume_semicolon()
        return ReturnStatement(value)

    # *** NEW METHOD ***
    def _parse_print(self):
        self._consume(TokenType.PRINT)
        self._consume(TokenType.LPAREN)
        args = []
        while self.current_token.type != TokenType.RPAREN:
            args.append(self._parse_expression())
            if self.current_token.type == TokenType.COMMA:
                self._advance()
        self._consume(TokenType.RPAREN)
        self._consume_semicolon()
        return PrintStatement(args)

    # *** NEW HELPER ***
    def _consume_semicolon(self):
        if self.current_token and self.current_token.type == TokenType.SEMICOLON:
            self._advance()

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
            prec = {
                TokenType.MULTIPLY: 3,
                TokenType.DIVIDE: 3,
                TokenType.PLUS: 2,
                TokenType.MINUS: 2,
                TokenType.EQUALS: 1,
                TokenType.NOT_EQUALS: 1,
                TokenType.LESS_THAN: 1,
                TokenType.GREATER_THAN: 1,
            }.get(token.type, 0)
            if prec < min_precedence:
                break
            self._advance()
            right = self._parse_binary_expression(prec + 1)
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
            ident_name = token.value
            self._advance()
            if self.current_token and self.current_token.type == TokenType.LBRACKET:
                self._advance()
                index = self._parse_expression()
                self._consume(TokenType.RBRACKET)
                return ArrayIndex(Identifier(ident_name), index)
            elif self.current_token and self.current_token.type == TokenType.LBRACE:
                self._advance()
                fields = []
                while self.current_token.type != TokenType.RBRACE:
                    field_name = self._consume(TokenType.IDENTIFIER).value
                    self._consume(TokenType.COLON)
                    field_value = self._parse_expression()
                    fields.append(StructField(field_name, field_value))
                    if self.current_token.type == TokenType.COMMA:
                        self._advance()
                self._consume(TokenType.RBRACE)
                return StructLiteral(fields)
            elif self.current_token and self.current_token.type == TokenType.LPAREN:
                return self._parse_call(ident_name)
            elif self.current_token and self.current_token.type == TokenType.DOT:
                self._advance()
                field_name = self._consume(TokenType.IDENTIFIER).value
                return StructFieldAccess(Identifier(ident_name), field_name)
            else:
                return Identifier(ident_name)
        if token.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN)
            return expr
        if token.type == TokenType.LBRACE:
            return self._parse_struct_literal()
        if token.type == TokenType.LBRACKET:
            return self._parse_array_literal()
        raise SyntaxError(f"Unexpected token '{token.value}' in expression")

    def _parse_array_literal(self):
        self._consume(TokenType.LBRACKET)
        elems = []
        while self.current_token.type != TokenType.RBRACKET:
            elems.append(self._parse_expression())
            if self.current_token.type == TokenType.COMMA:
                self._advance()
        self._consume(TokenType.RBRACKET)
        return ArrayLiteral(elems)

    def _parse_struct_literal(self):
        self._consume(TokenType.LBRACE)
        if self.current_token.type == TokenType.IDENTIFIER and self._peek_token() and self._peek_token().type == TokenType.COLON:
            fields = []
            while self.current_token.type != TokenType.RBRACE:
                name = self._consume(TokenType.IDENTIFIER).value
                self._consume(TokenType.COLON)
                value = self._parse_expression()
                fields.append(StructField(name, value))
                if self.current_token.type == TokenType.COMMA:
                    self._advance()
            self._consume(TokenType.RBRACE)
            return StructLiteral(fields)
        elems = []
        while self.current_token.type != TokenType.RBRACE:
            elems.append(self._parse_expression())
            if self.current_token.type == TokenType.COMMA:
                self._advance()
        self._consume(TokenType.RBRACE)
        return ArrayLiteral(elems)

    def _parse_call(self, func_name):
        self._consume(TokenType.LPAREN)
        args = []
        while self.current_token.type != TokenType.RPAREN:
            args.append(self._parse_expression())
            if self.current_token.type == TokenType.COMMA:
                self._advance()
        self._consume(TokenType.RPAREN)
        return CallExpression(func_name, args)

    def _consume(self, expected):
        if self.current_token.type != expected:
            raise SyntaxError(f"Expected {expected}, got {self.current_token.type}")
        tok = self.current_token
        self._advance()
        return tok

    def _advance(self):
        self.position += 1
        self.current_token = self.tokens[self.position] if self.position < len(self.tokens) else None

    def _peek_token(self):
        if self.position + 1 < len(self.tokens):
            return self.tokens[self.position + 1]
        return None