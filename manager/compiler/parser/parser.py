from typing import List, Optional

try:
    from compiler.lexer.tokens import Token, TokenType
    from compiler.parser.ast import (
        ASTNode,
        Program,
        AnalysisDeclaration,
        FunctionCall,
        Argument,
        AgentDeclaration,
        FunctionDeclaration,
        StructDeclaration,
        LetStatement,
        ReturnStatement,
        PrintStatement,
        IfStatement,
        WhileStatement,
        ForStatement,
        BinaryOperation,
        StringLiteral,
        NumberLiteral,
        Identifier,
        CallExpression,
    )
    from compiler.diagnostics.diagnostics import DiagnosticReporter, DiagnosticCode
except (ImportError, ModuleNotFoundError):
    from lexer.tokens import Token, TokenType
    from parser.ast import (
        ASTNode,
        Program,
        AnalysisDeclaration,
        FunctionCall,
        Argument,
        AgentDeclaration,
        FunctionDeclaration,
        StructDeclaration,
        LetStatement,
        ReturnStatement,
        PrintStatement,
        IfStatement,
        WhileStatement,
        ForStatement,
        BinaryOperation,
        StringLiteral,
        NumberLiteral,
        Identifier,
        CallExpression,
    )
    from diagnostics.diagnostics import DiagnosticReporter, DiagnosticCode


class ParseError(Exception):
    def __init__(self, message: str, token: Optional[Token] = None):
        super().__init__(message)
        self.token = token


class Parser:
    def __init__(
        self,
        tokens: List[Token],
        source: str = "",
        filename: str = "<input>",
        reporter: Optional[DiagnosticReporter] = None,
    ):
        self.tokens = tokens
        self.position = 0
        self.source = source
        self.filename = filename
        self.reporter = reporter or DiagnosticReporter(source, filename)
        self.current_token: Token = self.tokens[0] if tokens else Token(TokenType.EOF, "EOF")

    def parse(self) -> Program:
        declarations: List[ASTNode] = []

        while self.current_token and self.current_token.type != TokenType.EOF:
            try:
                if self.current_token.type == TokenType.ANALYSIS:
                    declarations.append(self._parse_analysis())
                elif self.current_token.type == TokenType.AGENT:
                    declarations.append(self._parse_agent())
                elif self.current_token.type == TokenType.FUNCTION:
                    declarations.append(self._parse_function_declaration())
                elif self.current_token.type == TokenType.STRUCT:
                    declarations.append(self._parse_struct_declaration())
                else:
                    tok = self.current_token
                    self.reporter.error(
                        code=DiagnosticCode.EXPECTED_ANALYSIS,
                        message=f"Expected 'analysis' block, found unexpected token '{tok.value}'",
                        line=tok.line,
                        column=tok.column,
                        offset=tok.offset,
                        length=tok.length,
                        help_text="Start your forensic script with `analysis \"Analysis Name\" { ... }`",
                    )
                    self._advance()
            except ParseError as e:
                if not self.reporter.has_errors():
                    tok = e.token or self.current_token
                    self.reporter.error(
                        code=DiagnosticCode.SYNTAX_ERROR,
                        message=str(e),
                        line=tok.line,
                        column=tok.column,
                        offset=tok.offset,
                        length=tok.length,
                    )
                self._synchronize()

        return Program(declarations, line=1, column=1)

    def _parse_analysis(self) -> AnalysisDeclaration:
        start_tok = self._consume(TokenType.ANALYSIS)
        
        # Expect analysis name (STRING)
        if self.current_token.type != TokenType.STRING:
            tok = self.current_token
            self.reporter.error(
                code=DiagnosticCode.EXPECTED_STRING,
                message=f"Expected analysis name string, found '{tok.value}'",
                line=tok.line,
                column=tok.column,
                offset=tok.offset,
                length=tok.length,
                help_text='Specify a name for the analysis, e.g. `analysis "System Investigation" { ... }`',
            )
            raise ParseError("Expected analysis name string", tok)

        name_tok = self._consume(TokenType.STRING)
        name = name_tok.value

        # Expect '{'
        if self.current_token.type != TokenType.LBRACE:
            tok = self.current_token
            self.reporter.error(
                code=DiagnosticCode.EXPECTED_LBRACE,
                message=f"Expected '{{' after analysis name, found '{tok.value}'",
                line=tok.line,
                column=tok.column,
                offset=tok.offset,
                length=tok.length,
                help_text="Open the analysis block with `{`.",
            )
            raise ParseError("Expected '{'", tok)

        self._consume(TokenType.LBRACE)

        statements: List[ASTNode] = []
        while self.current_token.type != TokenType.RBRACE and self.current_token.type != TokenType.EOF:
            stmt = self._parse_analysis_statement()
            if stmt:
                statements.append(stmt)

        if self.current_token.type != TokenType.RBRACE:
            tok = self.current_token
            self.reporter.error(
                code=DiagnosticCode.EXPECTED_RBRACE,
                message="Expected '}' to close analysis block",
                line=tok.line,
                column=tok.column,
                offset=tok.offset,
                length=tok.length,
                help_text="Close the analysis block with `}`.",
            )
            raise ParseError("Expected '}'", tok)

        self._consume(TokenType.RBRACE)
        return AnalysisDeclaration(name=name, statements=statements, line=start_tok.line, column=start_tok.column, offset=start_tok.offset)

    def _parse_analysis_statement(self) -> Optional[FunctionCall]:
        if self.current_token.type == TokenType.LET:
            return self._parse_let()

        call = self._parse_forensic_function_call()
        
        # Check for semicolon
        if self.current_token.type != TokenType.SEMICOLON:
            prev_tok = self._previous_token()
            err_line = prev_tok.line if prev_tok else self.current_token.line
            err_col = (prev_tok.column + prev_tok.length) if prev_tok else self.current_token.column
            err_pos = (prev_tok.offset + prev_tok.length) if prev_tok else self.current_token.offset
            
            self.reporter.error(
                code=DiagnosticCode.EXPECTED_SEMICOLON,
                message="Expected ';'",
                line=err_line,
                column=err_col,
                offset=err_pos,
                length=1,
                help_text="Add a semicolon `;` at the end of the statement.",
            )
            raise ParseError("Expected ';'", self.current_token)

        self._consume(TokenType.SEMICOLON)
        return call

    def _parse_forensic_function_call(self) -> FunctionCall:
        tok = self.current_token
        if tok.type != TokenType.IDENTIFIER:
            self.reporter.error(
                code=DiagnosticCode.EXPECTED_IDENTIFIER,
                message=f"Expected forensic namespace identifier, found '{tok.value}'",
                line=tok.line,
                column=tok.column,
                offset=tok.offset,
                length=tok.length,
                help_text="Forensic calls must be of the form `namespace.function()`, e.g. `system.info()`",
            )
            raise ParseError("Expected identifier", tok)

        namespace_tok = self._consume(TokenType.IDENTIFIER)
        namespace = str(namespace_tok.value)

        # Expect DOT '.'
        if self.current_token.type != TokenType.DOT:
            tok = self.current_token
            self.reporter.error(
                code=DiagnosticCode.MALFORMED_CALL,
                message=f"Expected '.' after namespace '{namespace}', found '{tok.value}'",
                line=tok.line,
                column=tok.column,
                offset=tok.offset,
                length=tok.length,
                help_text=f"Use `{namespace}.<function>()` to call a forensic function.",
            )
            raise ParseError("Expected '.'", tok)

        self._consume(TokenType.DOT)

        # Expect function identifier
        if self.current_token.type != TokenType.IDENTIFIER:
            tok = self.current_token
            self.reporter.error(
                code=DiagnosticCode.EXPECTED_IDENTIFIER,
                message=f"Expected function name after '{namespace}.', found '{tok.value}'",
                line=tok.line,
                column=tok.column,
                offset=tok.offset,
                length=tok.length,
            )
            raise ParseError("Expected function name", tok)

        func_tok = self._consume(TokenType.IDENTIFIER)
        func_name = str(func_tok.value)

        # Expect '('
        if self.current_token.type != TokenType.LPAREN:
            tok = self.current_token
            self.reporter.error(
                code=DiagnosticCode.EXPECTED_LPAREN,
                message=f"Expected '(' after '{namespace}.{func_name}', found '{tok.value}'",
                line=tok.line,
                column=tok.column,
                offset=tok.offset,
                length=tok.length,
                help_text=f"Function calls require parentheses: `{namespace}.{func_name}()`",
            )
            raise ParseError("Expected '('", tok)

        self._consume(TokenType.LPAREN)

        # Arguments: arguments?
        args: List[Argument] = []
        if self.current_token.type != TokenType.RPAREN:
            args.append(self._parse_argument())
            while self.current_token.type == TokenType.COMMA:
                self._consume(TokenType.COMMA)
                args.append(self._parse_argument())

        # Expect ')'
        if self.current_token.type != TokenType.RPAREN:
            tok = self.current_token
            self.reporter.error(
                code=DiagnosticCode.EXPECTED_RPAREN,
                message=f"Expected ')' after arguments, found '{tok.value}'",
                line=tok.line,
                column=tok.column,
                offset=tok.offset,
                length=tok.length,
            )
            raise ParseError("Expected ')'", tok)

        self._consume(TokenType.RPAREN)

        return FunctionCall(
            namespace=namespace,
            function=func_name,
            arguments=args,
            line=namespace_tok.line,
            column=namespace_tok.column,
            offset=namespace_tok.offset,
        )

    def _parse_argument(self) -> Argument:
        tok = self.current_token
        if tok.type == TokenType.STRING:
            self._consume(TokenType.STRING)
            return Argument(value=str(tok.value), arg_type="string", line=tok.line, column=tok.column, offset=tok.offset)
        elif tok.type == TokenType.NUMBER:
            self._consume(TokenType.NUMBER)
            return Argument(value=tok.value, arg_type="number", line=tok.line, column=tok.column, offset=tok.offset)
        elif tok.type == TokenType.BOOLEAN:
            self._consume(TokenType.BOOLEAN)
            return Argument(value=tok.value, arg_type="boolean", line=tok.line, column=tok.column, offset=tok.offset)
        elif tok.type == TokenType.IDENTIFIER:
            self._consume(TokenType.IDENTIFIER)
            return Argument(value=tok.value, arg_type="identifier", line=tok.line, column=tok.column, offset=tok.offset)
        else:
            self.reporter.error(
                code=DiagnosticCode.SYNTAX_ERROR,
                message=f"Expected literal argument (string, number, or boolean), found '{tok.value}'",
                line=tok.line,
                column=tok.column,
                offset=tok.offset,
                length=tok.length,
                help_text="Forensic function arguments must be literals or variables (e.g. \"./evidence\", 100, true, pid).",
            )
            raise ParseError("Expected literal argument", tok)

    def _synchronize(self):
        while self.current_token and self.current_token.type != TokenType.EOF:
            if self.current_token.type in (TokenType.ANALYSIS, TokenType.AGENT, TokenType.FUNCTION, TokenType.STRUCT):
                return
            if self.current_token.type == TokenType.SEMICOLON:
                self._advance()
                return
            self._advance()

    # ==========================================================================
    # Legacy parser methods for Agent / Function / Struct compatibility
    # ==========================================================================

    def _parse_agent(self):
        start_tok = self._consume(TokenType.AGENT)
        name = self._consume(TokenType.IDENTIFIER).value

        if self.current_token and self.current_token.type == TokenType.ASSIGN:
            self._advance()

        self._consume(TokenType.LBRACE)
        body = []
        while self.current_token.type != TokenType.RBRACE and self.current_token.type != TokenType.EOF:
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
                if self._peek_token() and self._peek_token().type == TokenType.LPAREN:
                    call_expr = self._parse_call(self._consume(TokenType.IDENTIFIER).value)
                    self._consume_semicolon_optional()
                    body.append(call_expr)
                else:
                    name_var = self._consume(TokenType.IDENTIFIER).value
                    self._consume(TokenType.ASSIGN)
                    value = self._parse_expression()
                    self._consume_semicolon_optional()
                    body.append(LetStatement(name_var, value))
            else:
                self._advance()
        if self.current_token.type == TokenType.RBRACE:
            self._consume(TokenType.RBRACE)
        return AgentDeclaration(name, body, line=start_tok.line, column=start_tok.column)

    def _parse_function_declaration(self):
        start_tok = self._consume(TokenType.FUNCTION)
        func_name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.LPAREN)
        params = []
        while self.current_token.type != TokenType.RPAREN and self.current_token.type != TokenType.EOF:
            params.append(self._consume(TokenType.IDENTIFIER).value)
            if self.current_token.type == TokenType.COMMA:
                self._advance()
        self._consume(TokenType.RPAREN)
        self._consume(TokenType.LBRACE)
        body = []
        while self.current_token.type != TokenType.RBRACE and self.current_token.type != TokenType.EOF:
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
                if self._peek_token() and self._peek_token().type == TokenType.LPAREN:
                    call_expr = self._parse_call(self._consume(TokenType.IDENTIFIER).value)
                    self._consume_semicolon_optional()
                    body.append(call_expr)
                else:
                    name_var = self._consume(TokenType.IDENTIFIER).value
                    self._consume(TokenType.ASSIGN)
                    value = self._parse_expression()
                    self._consume_semicolon_optional()
                    body.append(LetStatement(name_var, value))
            else:
                self._advance()
        if self.current_token.type == TokenType.RBRACE:
            self._consume(TokenType.RBRACE)
        return FunctionDeclaration(func_name, params, body, line=start_tok.line, column=start_tok.column)

    def _parse_struct_declaration(self):
        start_tok = self._consume(TokenType.STRUCT)
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.LBRACE)
        fields = []
        while self.current_token.type != TokenType.RBRACE and self.current_token.type != TokenType.EOF:
            fields.append(self._consume(TokenType.IDENTIFIER).value)
            if self.current_token.type == TokenType.COMMA:
                self._advance()
        if self.current_token.type == TokenType.RBRACE:
            self._consume(TokenType.RBRACE)
        return StructDeclaration(name, fields, line=start_tok.line, column=start_tok.column)

    def _parse_let(self):
        self._consume(TokenType.LET)
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.ASSIGN)
        value = self._parse_expression()
        self._consume_semicolon_optional()
        return LetStatement(name, value)

    def _parse_return(self):
        self._consume(TokenType.RETURN)
        value = self._parse_expression()
        self._consume_semicolon_optional()
        return ReturnStatement(value)

    def _parse_print(self):
        self._consume(TokenType.PRINT)
        self._consume(TokenType.LPAREN)
        args = []
        while self.current_token.type != TokenType.RPAREN and self.current_token.type != TokenType.EOF:
            args.append(self._parse_expression())
            if self.current_token.type == TokenType.COMMA:
                self._advance()
        self._consume(TokenType.RPAREN)
        self._consume_semicolon_optional()
        return PrintStatement(args)

    def _parse_if(self):
        self._consume(TokenType.IF)
        cond = self._parse_expression()
        self._consume(TokenType.LBRACE)
        then_body = []
        while self.current_token.type != TokenType.RBRACE and self.current_token.type != TokenType.EOF:
            then_body.append(self._parse_statement_simple())
        self._consume(TokenType.RBRACE)
        else_body = []
        if self.current_token.type == TokenType.ELSE:
            self._consume(TokenType.ELSE)
            self._consume(TokenType.LBRACE)
            while self.current_token.type != TokenType.RBRACE and self.current_token.type != TokenType.EOF:
                else_body.append(self._parse_statement_simple())
            self._consume(TokenType.RBRACE)
        return IfStatement(cond, then_body, else_body)

    def _parse_while(self):
        self._consume(TokenType.WHILE)
        cond = self._parse_expression()
        self._consume(TokenType.LBRACE)
        body = []
        while self.current_token.type != TokenType.RBRACE and self.current_token.type != TokenType.EOF:
            body.append(self._parse_statement_simple())
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
        while self.current_token.type != TokenType.RBRACE and self.current_token.type != TokenType.EOF:
            body.append(self._parse_statement_simple())
        self._consume(TokenType.RBRACE)
        return ForStatement(var, start, end, body)

    def _parse_statement_simple(self):
        if self.current_token.type == TokenType.LET:
            return self._parse_let()
        elif self.current_token.type == TokenType.RETURN:
            return self._parse_return()
        elif self.current_token.type == TokenType.PRINT:
            return self._parse_print()
        elif self.current_token.type == TokenType.IDENTIFIER:
            if self._peek_token() and self._peek_token().type == TokenType.LPAREN:
                call_expr = self._parse_call(self._consume(TokenType.IDENTIFIER).value)
                self._consume_semicolon_optional()
                return call_expr
            else:
                name_var = self._consume(TokenType.IDENTIFIER).value
                self._consume(TokenType.ASSIGN)
                val = self._parse_expression()
                self._consume_semicolon_optional()
                return LetStatement(name_var, val)
        self._advance()
        return None

    def _parse_expression(self):
        return self._parse_logical_or()

    def _parse_logical_or(self):
        left = self._parse_logical_and()
        while self.current_token.type == TokenType.OR:
            op = self.current_token.value
            self._advance()
            left = BinaryOperation(left, op, self._parse_logical_and())
        return left

    def _parse_logical_and(self):
        left = self._parse_equality()
        while self.current_token.type == TokenType.AND:
            op = self.current_token.value
            self._advance()
            left = BinaryOperation(left, op, self._parse_equality())
        return left

    def _parse_equality(self):
        left = self._parse_primary()
        while self.current_token.type in (TokenType.EQUALS, TokenType.NOT_EQUALS, TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, TokenType.DIVIDE):
            op = self.current_token.value
            self._advance()
            right = self._parse_primary()
            left = BinaryOperation(left, op, right)
        return left

    def _parse_primary(self):
        tok = self.current_token
        if tok.type == TokenType.NUMBER:
            self._advance()
            return NumberLiteral(tok.value, tok.line, tok.column, tok.offset)
        elif tok.type == TokenType.STRING:
            self._advance()
            return StringLiteral(tok.value, tok.line, tok.column, tok.offset)
        elif tok.type == TokenType.BOOLEAN:
            self._advance()
            return tok.value
        elif tok.type == TokenType.IDENTIFIER:
            name = tok.value
            self._advance()
            if self.current_token.type == TokenType.LPAREN:
                return self._parse_call(name)
            return Identifier(name, tok.line, tok.column, tok.offset)
        self._advance()
        return None

    def _parse_call(self, name):
        self._consume(TokenType.LPAREN)
        args = []
        while self.current_token.type != TokenType.RPAREN and self.current_token.type != TokenType.EOF:
            args.append(self._parse_expression())
            if self.current_token.type == TokenType.COMMA:
                self._advance()
        self._consume(TokenType.RPAREN)
        return CallExpression(name, args)

    def _consume_semicolon_optional(self):
        if self.current_token.type == TokenType.SEMICOLON:
            self._advance()

    def _consume(self, expected_type: TokenType) -> Token:
        if self.current_token.type != expected_type:
            tok = self.current_token
            raise ParseError(f"Expected {expected_type.name}, found {tok.type.name} ('{tok.value}')", tok)
        tok = self.current_token
        self._advance()
        return tok

    def _advance(self):
        self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = Token(TokenType.EOF, "EOF", self.tokens[-1].line if self.tokens else 1, self.tokens[-1].column if self.tokens else 1)

    def _peek_token(self) -> Optional[Token]:
        if self.position + 1 < len(self.tokens):
            return self.tokens[self.position + 1]
        return None

    def _previous_token(self) -> Optional[Token]:
        if self.position > 0 and self.tokens:
            return self.tokens[self.position - 1]
        return None