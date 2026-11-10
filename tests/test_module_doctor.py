"""Offline diagnostics and actual module entry-point checks."""
import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from mukimov import __version__, cli


class TestDoctor(unittest.TestCase):
    def run_doctor(self, command="launcher", missing=None):
        output = io.StringIO()
        with patch.object(cli.shutil, "which", return_value=command), \
             patch.object(cli.importlib.util, "find_spec", side_effect=lambda name: None if name == missing else object()), \
             patch.object(cli.Path, "is_file", return_value=False), \
             patch.object(cli, "get_latest_version", side_effect=AssertionError("doctor must stay offline")), \
             redirect_stdout(output):
            code = cli.main(["doctor"])
        return code, output.getvalue()

    def test_healthy_report(self):
        code, output = self.run_doctor()
        self.assertEqual(code, 0)
        self.assertIn("Version: " + __version__, output)
        self.assertIn(sys.executable, output)
        self.assertIn("Scripts:", output)
        self.assertIn("Command in PATH: launcher", output)
        self.assertIn("Result: OK", output)

    def test_missing_launcher_has_module_workaround(self):
        code, output = self.run_doctor(command=None)
        self.assertEqual(code, 1)
        self.assertIn("Command in PATH: MISSING", output)
        self.assertIn("-m mukimov --version", output)

    def test_missing_dependency(self):
        for name, label in (
            ("pip", "pip"),
            ("packaging", "packaging"),
            ("dotenv", "python-dotenv"),
            ("markdown_it", "markdown-it-py"),
            ("wcwidth", "wcwidth"),
            ("jinja2", "Jinja2"),
        ):
            with self.subTest(name=name):
                code, output = self.run_doctor(missing=name)
                self.assertEqual(code, 1)
                self.assertIn(label + ": MISSING", output)

    def test_foreign_launcher_warning(self):
        output = io.StringIO()
        with patch.object(cli.shutil, "which", return_value="foreign-launcher"), \
             patch.object(cli.importlib.util, "find_spec", return_value=object()), \
             patch.object(cli.Path, "is_file", return_value=True), redirect_stdout(output):
            code = cli.main(["doctor"])
        self.assertEqual(code, 1)
        self.assertIn("outside this interpreter", output.getvalue())


class TestModule(unittest.TestCase):
    def run_module(self, *args):
        return subprocess.run([sys.executable, "-m", "mukimov", *args],
                              cwd=Path(__file__).resolve().parent.parent,
                              capture_output=True, text=True, encoding="utf-8", timeout=30)

    def test_module_version(self):
        result = self.run_module("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "mukimov " + __version__)

    def test_module_doctor(self):
        result = self.run_module("doctor")
        self.assertIn(result.returncode, (0, 1), result.stderr)
        self.assertIn("mukimov doctor", result.stdout)
        self.assertIn("Version: " + __version__, result.stdout)


if __name__ == "__main__":
    unittest.main()
