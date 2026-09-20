"""
Unit Tests for JOCKY Semantic Analyzer
"""
import unittest
from compiler.compiler import Compiler
from compiler.diagnostics.diagnostics import DiagnosticCode


class TestSemantic(unittest.TestCase):
    def test_semantic_valid_functions(self):
        source = '''
        analysis "Valid Investigation" {
            system.info();
            system.users();
            processes.list();
            processes.details(1024);
            network.interfaces();
            network.connections();
            network.routes();
            network.dns();
            filesystem.metadata("/etc/hosts");
            filesystem.hash("./evidence.raw");
        }
        '''
        compiler = Compiler()
        result = compiler.compile(source)
        self.assertTrue(result.success)
        self.assertEqual(len(result.diagnostics), 0)
        self.assertIsNotNone(result.ir)
        self.assertEqual(len(result.ir["operations"]), 10)

    def test_semantic_e2001_unknown_namespace(self):
        source = '''
        analysis "Bad Namespace" {
            storage.info();
        }
        '''
        compiler = Compiler()
        result = compiler.compile(source)
        self.assertFalse(result.success)
        self.assertTrue(any(d.code == DiagnosticCode.UNKNOWN_NAMESPACE for d in result.diagnostics))
        err = [d for d in result.diagnostics if d.code == DiagnosticCode.UNKNOWN_NAMESPACE][0]
        self.assertIn("Unknown namespace 'storage'.", err.message)

    def test_semantic_e2002_unknown_function(self):
        source = '''
        analysis "Bad Function" {
            network.fake();
        }
        '''
        compiler = Compiler()
        result = compiler.compile(source)
        self.assertFalse(result.success)
        self.assertTrue(any(d.code == DiagnosticCode.UNKNOWN_FUNCTION for d in result.diagnostics))
        err = [d for d in result.diagnostics if d.code == DiagnosticCode.UNKNOWN_FUNCTION][0]
        self.assertIn("Unknown forensic function 'network.fake'.", err.message)
        self.assertIsNotNone(err.help_text)
        self.assertIn("network.interfaces()", err.help_text)

    def test_semantic_e2003_wrong_argument_count(self):
        # network.connections expects 0 arguments, but 1 was provided
        source = '''
        analysis "Wrong Arg Count" {
            network.connections(123);
        }
        '''
        compiler = Compiler()
        result = compiler.compile(source)
        self.assertFalse(result.success)
        self.assertTrue(any(d.code == DiagnosticCode.WRONG_ARGUMENT_COUNT for d in result.diagnostics))
        err = [d for d in result.diagnostics if d.code == DiagnosticCode.WRONG_ARGUMENT_COUNT][0]
        self.assertIn("expects 0 arguments, but 1 argument was provided", err.message)

    def test_semantic_e2004_missing_argument(self):
        # processes.details expects 1 argument, but 0 provided
        source = '''
        analysis "Missing Arg" {
            processes.details();
        }
        '''
        compiler = Compiler()
        result = compiler.compile(source)
        self.assertFalse(result.success)
        self.assertTrue(any(d.code == DiagnosticCode.MISSING_ARGUMENT for d in result.diagnostics))
        err = [d for d in result.diagnostics if d.code == DiagnosticCode.MISSING_ARGUMENT][0]
        self.assertIn("expects 1 argument", err.message)
        self.assertIn("processes.details(pid)", err.help_text)

    def test_semantic_e2005_wrong_argument_type(self):
        # processes.details requires number, but string provided
        source = '''
        analysis "Wrong Arg Type" {
            processes.details("chrome");
        }
        '''
        compiler = Compiler()
        result = compiler.compile(source)
        self.assertFalse(result.success)
        self.assertTrue(any(d.code == DiagnosticCode.WRONG_ARGUMENT_TYPE for d in result.diagnostics))
        err = [d for d in result.diagnostics if d.code == DiagnosticCode.WRONG_ARGUMENT_TYPE][0]
        self.assertIn("Invalid argument type for 'processes.details'.", err.message)
        self.assertIn("number", err.help_text)
        self.assertIn("string", err.help_text)


if __name__ == "__main__":
    unittest.main()
