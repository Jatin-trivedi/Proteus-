"""
Unit Tests for JOCKY Parser
"""
import unittest
from compiler.lexer.tokenizer import Lexer
from compiler.parser.parser import Parser
from compiler.parser.ast import AnalysisBlock, FunctionCall, Argument
from compiler.diagnostics.diagnostics import DiagnosticReporter, DiagnosticCode


class TestParser(unittest.TestCase):
    def test_parser_valid_analysis_block(self):
        source = '''
        analysis "System Investigation" {
            system.info();
            filesystem.hash("./evidence");
        }
        '''
        reporter = DiagnosticReporter(source)
        lexer = Lexer(source, reporter=reporter)
        tokens = lexer.tokenize()
        parser = Parser(tokens, source=source, reporter=reporter)
        ast = parser.parse()

        self.assertFalse(reporter.has_errors())
        self.assertEqual(len(ast.body), 1)
        decl = ast.body[0]
        self.assertIsInstance(decl, AnalysisBlock)
        self.assertEqual(decl.name, "System Investigation")
        self.assertEqual(len(decl.statements), 2)

        # statement 1: system.info()
        stmt1 = decl.statements[0]
        self.assertIsInstance(stmt1, FunctionCall)
        self.assertEqual(stmt1.namespace, "system")
        self.assertEqual(stmt1.function, "info")
        self.assertEqual(len(stmt1.arguments), 0)

        # statement 2: filesystem.hash("./evidence")
        stmt2 = decl.statements[1]
        self.assertIsInstance(stmt2, FunctionCall)
        self.assertEqual(stmt2.namespace, "filesystem")
        self.assertEqual(stmt2.function, "hash")
        self.assertEqual(len(stmt2.arguments), 1)
        self.assertEqual(stmt2.arguments[0].value, "./evidence")
        self.assertEqual(stmt2.arguments[0].arg_type, "string")

    def test_parser_various_arguments(self):
        source = '''
        analysis "Arg Test" {
            processes.details(1234);
            custom.flag(true);
            custom.multi("path", 42, false);
        }
        '''
        reporter = DiagnosticReporter(source)
        lexer = Lexer(source, reporter=reporter)
        tokens = lexer.tokenize()
        parser = Parser(tokens, source=source, reporter=reporter)
        ast = parser.parse()

        decl = ast.body[0]
        self.assertEqual(len(decl.statements), 3)

        self.assertEqual(decl.statements[0].arguments[0].value, 1234)
        self.assertEqual(decl.statements[0].arguments[0].arg_type, "number")

        self.assertIs(decl.statements[1].arguments[0].value, True)
        self.assertEqual(decl.statements[1].arguments[0].arg_type, "boolean")

        args = decl.statements[2].arguments
        self.assertEqual(len(args), 3)
        self.assertEqual(args[0].value, "path")
        self.assertEqual(args[0].arg_type, "string")
        self.assertEqual(args[1].value, 42)
        self.assertEqual(args[1].arg_type, "number")
        self.assertIs(args[2].value, False)
        self.assertEqual(args[2].arg_type, "boolean")

    def test_parser_missing_semicolon(self):
        source = '''
        analysis "Test" {
            system.info()
            network.connections();
        }
        '''
        reporter = DiagnosticReporter(source)
        lexer = Lexer(source, reporter=reporter)
        tokens = lexer.tokenize()
        parser = Parser(tokens, source=source, reporter=reporter)
        ast = parser.parse()

        self.assertTrue(reporter.has_errors())
        self.assertTrue(any(d.code == DiagnosticCode.EXPECTED_SEMICOLON for d in reporter.diagnostics))
        error = [d for d in reporter.diagnostics if d.code == DiagnosticCode.EXPECTED_SEMICOLON][0]
        self.assertEqual(error.line, 3)

    def test_parser_missing_braces(self):
        source = '''
        analysis "Test"
            system.info();
        }
        '''
        reporter = DiagnosticReporter(source)
        lexer = Lexer(source, reporter=reporter)
        tokens = lexer.tokenize()
        parser = Parser(tokens, source=source, reporter=reporter)
        ast = parser.parse()

        self.assertTrue(reporter.has_errors())
        self.assertTrue(any(d.code == DiagnosticCode.EXPECTED_LBRACE for d in reporter.diagnostics))

    def test_parser_ast_json_serialization(self):
        source = '''
        analysis "Test" {
            system.info();
        }
        '''
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        d = ast.to_dict()
        self.assertEqual(d["type"], "Program")
        self.assertIn("analyses", d)
        self.assertEqual(d["analyses"][0]["type"], "AnalysisBlock")
        self.assertEqual(d["analyses"][0]["name"], "Test")
        self.assertEqual(d["analyses"][0]["statements"][0]["namespace"], "system")
        self.assertEqual(d["analyses"][0]["statements"][0]["function"], "info")


if __name__ == "__main__":
    unittest.main()
