"""
Unit Tests for JOCKY Lexer
"""
import unittest
from compiler.lexer.tokenizer import Lexer
from compiler.lexer.tokens import TokenType


class TestLexer(unittest.TestCase):
    def test_lexer_keywords_and_identifiers(self):
        source = "analysis agent let return if else while for in to true false function struct print"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        expected_types = [
            TokenType.ANALYSIS,
            TokenType.AGENT,
            TokenType.LET,
            TokenType.RETURN,
            TokenType.IF,
            TokenType.ELSE,
            TokenType.WHILE,
            TokenType.FOR,
            TokenType.IN,
            TokenType.TO,
            TokenType.BOOLEAN,
            TokenType.BOOLEAN,
            TokenType.FUNCTION,
            TokenType.STRUCT,
            TokenType.PRINT,
            TokenType.EOF,
        ]
        self.assertEqual([t.type for t in tokens], expected_types)

    def test_lexer_literals(self):
        source = '"hello world" "escaped \\" quote" 123 45.67 true false'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        self.assertEqual(tokens[0].type, TokenType.STRING)
        self.assertEqual(tokens[0].value, "hello world")

        self.assertEqual(tokens[1].type, TokenType.STRING)
        self.assertEqual(tokens[1].value, 'escaped " quote')

        self.assertEqual(tokens[2].type, TokenType.NUMBER)
        self.assertEqual(tokens[2].value, 123)

        self.assertEqual(tokens[3].type, TokenType.NUMBER)
        self.assertEqual(tokens[3].value, 45.67)

        self.assertEqual(tokens[4].type, TokenType.BOOLEAN)
        self.assertIs(tokens[4].value, True)

        self.assertEqual(tokens[5].type, TokenType.BOOLEAN)
        self.assertIs(tokens[5].value, False)

    def test_lexer_punctuation_and_operators(self):
        source = ". ; , ( ) { } = == != < > + - * /"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        expected_types = [
            TokenType.DOT,
            TokenType.SEMICOLON,
            TokenType.COMMA,
            TokenType.LPAREN,
            TokenType.RPAREN,
            TokenType.LBRACE,
            TokenType.RBRACE,
            TokenType.ASSIGN,
            TokenType.EQUALS,
            TokenType.NOT_EQUALS,
            TokenType.LESS_THAN,
            TokenType.GREATER_THAN,
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.MULTIPLY,
            TokenType.DIVIDE,
            TokenType.EOF,
        ]
        self.assertEqual([t.type for t in tokens], expected_types)

    def test_lexer_dot_function_call(self):
        source = "network.connections();"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        self.assertEqual(len(tokens), 7)
        self.assertEqual(tokens[0].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[0].value, "network")
        self.assertEqual(tokens[1].type, TokenType.DOT)
        self.assertEqual(tokens[2].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[2].value, "connections")
        self.assertEqual(tokens[3].type, TokenType.LPAREN)
        self.assertEqual(tokens[4].type, TokenType.RPAREN)
        self.assertEqual(tokens[5].type, TokenType.SEMICOLON)
        self.assertEqual(tokens[6].type, TokenType.EOF)

    def test_lexer_source_locations(self):
        source = 'analysis "Test" {\n    system.info();\n}'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # analysis -> line 1, col 1, offset 0
        self.assertEqual(tokens[0].line, 1)
        self.assertEqual(tokens[0].column, 1)
        self.assertEqual(tokens[0].offset, 0)

        # "Test" -> line 1, col 10, offset 9
        self.assertEqual(tokens[1].type, TokenType.STRING)
        self.assertEqual(tokens[1].line, 1)
        self.assertEqual(tokens[1].column, 10)

        # system -> line 2, col 5
        system_tok = [t for t in tokens if t.value == "system"][0]
        self.assertEqual(system_tok.line, 2)
        self.assertEqual(system_tok.column, 5)

    def test_lexer_comments(self):
        source = """
        # Full line comment
        // Another comment style
        system.info(); # inline comment
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        token_values = [t.value for t in tokens if t.type != TokenType.EOF]
        self.assertEqual(token_values, ["system", ".", "info", "(", ")", ";"])


if __name__ == "__main__":
    unittest.main()
