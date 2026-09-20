"""
Unit and Integration Tests for JOCKY CLI (Priority 3.5)
"""
import unittest
import subprocess
import json
import tempfile
import os
from pathlib import Path


class TestCLI(unittest.TestCase):
    def test_cli_compile_basic(self):
        cmd = ["python3", "-m", "compiler", "compile", "examples/network.jocky"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Compilation successful.", result.stdout)
        self.assertIn("Analysis:\nNetwork Investigation", result.stdout)
        self.assertIn("Operations:\n4", result.stdout)

        # Check default build output file
        ir_file = Path("build/network.ir.json")
        self.assertTrue(ir_file.exists())
        with open(ir_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["investigation"], "Network Investigation")
        self.assertEqual(len(data["operations"]), 4)

    def test_cli_compile_with_ir_flag(self):
        cmd = ["python3", "-m", "compiler", "compile", "examples/network.jocky", "--ir"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("---------------- IR -----------------", result.stdout)
        self.assertIn('"ir_type": "jocky_forensic_ir"', result.stdout)
        self.assertIn('"investigation": "Network Investigation"', result.stdout)

    def test_cli_compile_custom_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "custom_net.ir.json")
            cmd = [
                "python3",
                "-m",
                "compiler",
                "compile",
                "examples/network.jocky",
                "--output",
                out_file,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertTrue(os.path.isfile(out_file))

            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["version"], "1.0")
            self.assertEqual(data["investigation"], "Network Investigation")
            self.assertEqual(len(data["operations"]), 4)

    def test_cli_check_mode(self):
        cmd = ["python3", "-m", "compiler", "check", "examples/system.jocky"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Compilation successful.", result.stdout)

    def test_cli_complete_investigation_e2e(self):
        cmd = ["python3", "-m", "compiler", "compile", "examples/complete_investigation.jocky"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Analysis:\nComplete Investigation", result.stdout)
        self.assertIn("Operations:\n9", result.stdout)

        ir_file = Path("build/complete_investigation.ir.json")
        self.assertTrue(ir_file.exists())
        with open(ir_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["investigation"], "Complete Investigation")
        self.assertEqual(len(data["operations"]), 9)

        # Verify sequential IDs op-001..op-009
        expected_ids = [f"op-{i:03d}" for i in range(1, 10)]
        actual_ids = [op["id"] for op in data["operations"]]
        self.assertEqual(actual_ids, expected_ids)

        # Verify operation types and ordering
        expected_types = [
            "system.info",
            "system.users",
            "processes.list",
            "network.interfaces",
            "network.connections",
            "network.routes",
            "network.dns",
            "filesystem.metadata",
            "filesystem.hash",
        ]
        actual_types = [op["type"] for op in data["operations"]]
        self.assertEqual(actual_types, expected_types)

    def test_cli_invalid_program_fails_without_ir_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "should_not_exist.ir.json")
            cmd = [
                "python3",
                "-m",
                "compiler",
                "compile",
                "examples/invalid.jocky",
                "-o",
                out_file,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("JOCKY-E2002", result.stderr)
            self.assertIn("Compilation failed.", result.stderr)
            self.assertFalse(os.path.exists(out_file))

    def test_cli_determinism(self):
        cmd = ["python3", "-m", "compiler", "compile", "examples/complete_investigation.jocky"]
        res1 = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res1.returncode, 0)

        with open("build/complete_investigation.ir.json", "r", encoding="utf-8") as f:
            ir1 = json.load(f)

        res2 = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res2.returncode, 0)

        with open("build/complete_investigation.ir.json", "r", encoding="utf-8") as f:
            ir2 = json.load(f)

        self.assertEqual(ir1, ir2)


if __name__ == "__main__":
    unittest.main()
