"""Regression tests for real terminal input and the no-echo fallback."""

import getpass
import io
import os
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

from mukimov import stars


class TestFallback(unittest.TestCase):
    def test_unsafe_getpass_fallback_stops_before_reading(self):
        with patch("sys.stdin", io.StringIO("unused\n")) as stdin:
            with patch.object(getpass, "getpass", getpass.fallback_getpass):
                with self.assertRaisesRegex(RuntimeError, "echo disabled"):
                    stars()
            self.assertEqual(stdin.tell(), 0)


@unittest.skipUnless(sys.platform in ("linux", "darwin"), "requires a Unix PTY")
class TestUnixTerminal(unittest.TestCase):
    def run_terminal(self, keys, program):
        import pty
        import termios

        master, slave = pty.openpty()
        try:
            original = termios.tcgetattr(slave)
            with subprocess.Popen(
                [sys.executable, "-X", "utf8", "-c", program],
                stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            ) as proc:
                try:
                    deadline = time.monotonic() + 5
                    while termios.tcgetattr(slave)[3] & termios.ICANON:
                        if proc.poll() is not None or time.monotonic() >= deadline:
                            self.fail("Child did not put the terminal in raw mode")
                        time.sleep(0.01)
                    os.write(master, keys)
                    output, errors = proc.communicate(timeout=5)
                    self.assertEqual(proc.returncode, 0, errors.decode("utf-8"))
                    restored = termios.tcgetattr(slave)
                    if sys.platform == "darwin":
                        # Darwin sets PENDIN when canonical mode is restored.
                        # The kernel clears it when it processes pending input.
                        pending = getattr(termios, "PENDIN", 0x20000000)
                        restored[3] &= ~pending
                        original[3] &= ~pending
                    self.assertEqual(restored, original)
                    return output.decode("utf-8")
                finally:
                    if proc.poll() is None:
                        proc.kill()
                        proc.communicate()
        finally:
            os.close(master)
            os.close(slave)

    def test_unicode_paste_escape_and_backspace(self):
        output = self.run_terminal(
            b"\x1b[1;5D\x1b[200~" + "éx".encode("utf-8") + b"\x1b[201~\x7f\x1b\r",
            "from mukimov import stars; assert stars() == chr(233)",
        )
        self.assertEqual(output, "Password: **\b \b\n")

    def test_interrupt_restores_terminal(self):
        self.assertEqual(
            self.run_terminal(b"a\x03", "from mukimov import stars\n"
                              "try: stars()\nexcept KeyboardInterrupt: pass\n"
                              "else: raise AssertionError('expected interrupt')"),
            "Password: *\n",
        )
