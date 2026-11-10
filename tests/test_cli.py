"""Tests for mukimov.cli (mukimov --version / mukimov update)."""

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from mukimov import __version__, cli
from mukimov.update import UpdateCheckError


def run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(argv)
    return code, out.getvalue(), err.getvalue()


class TestVersionCmd(unittest.TestCase):
    def test_version_flag(self):
        code, out, _ = run_cli(["--version"])
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), f"mukimov {__version__}")

    def test_version_alias(self):
        code, out, _ = run_cli(["-V"])
        self.assertEqual(code, 0)
        self.assertIn(__version__, out)

    def test_version_needs_no_network(self):
        with mock.patch(
            "mukimov.update.fetch_latest_version",
            side_effect=AssertionError("must not touch network"),
        ):
            code, out, _ = run_cli(["--version"])
        self.assertEqual(code, 0)
        self.assertIn(__version__, out)


class TestUpdateCmd(unittest.TestCase):
    def test_up_to_date_no_pip_call(self):
        with mock.patch.object(cli, "get_latest_version", return_value=__version__):
            with mock.patch.object(
                cli.subprocess, "run", side_effect=AssertionError("pip must not run")
            ):
                code, out, _ = run_cli(["update"])
        self.assertEqual(code, 0)
        self.assertIn(__version__, out)
        self.assertTrue(
            "Already up to date" in out or "не требуется" in out,
            f"unexpected output: {out!r}",
        )

    def test_update_runs_same_python_pip_and_shows_versions(self):
        fake_proc = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch.object(cli, "get_latest_version", return_value="9.9.9"):
            with mock.patch.object(cli.subprocess, "run", return_value=fake_proc) as mrun:
                with mock.patch(
                    "importlib.metadata.version", return_value="9.9.9"
                ):
                    code, out, _ = run_cli(["update"])
        self.assertEqual(code, 0)
        self.assertIn(__version__, out)  # old version
        self.assertIn("9.9.9", out)  # new version
        self.assertIn("Updated", out)
        # Same interpreter: sys.executable -m pip ...
        cmd = mrun.call_args[0][0]
        self.assertEqual(cmd[:3], [sys.executable, "-m", "pip"])
        self.assertIn("mukimov==9.9.9", cmd)

    def test_update_does_not_report_success_when_pip_leaves_old_version(self):
        fake_proc = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch.object(cli, "get_latest_version", return_value="9.9.9"), \
                mock.patch.object(cli.subprocess, "run", return_value=fake_proc), \
                mock.patch("importlib.metadata.version", return_value=__version__):
            code, out, err = run_cli(["update"])
        self.assertEqual(code, 1)
        self.assertNotIn("Updated", out)
        self.assertIn(f"installed version is {__version__}", err)

    def test_update_network_error(self):
        with mock.patch.object(
            cli, "get_latest_version", side_effect=UpdateCheckError("offline")
        ):
            code, out, err = run_cli(["update"])
        self.assertEqual(code, 1)
        self.assertIn("Error", err)

    def test_update_pip_failure(self):
        fake_proc = mock.Mock(returncode=1, stdout="", stderr="boom")
        with mock.patch.object(cli, "get_latest_version", return_value="9.9.9"):
            with mock.patch.object(cli.subprocess, "run", return_value=fake_proc):
                code, out, err = run_cli(["update"])
        self.assertEqual(code, 1)
        self.assertIn("Error", err)


class TestNotify(unittest.TestCase):
    def test_notice_on_new_version(self):
        with mock.patch.object(cli, "_read_cache", return_value={"latest": "9.9.9"}):
            _, _, err = run_cli([])
        self.assertIn("New mukimov version available: 9.9.9", err)
        self.assertIn("mukimov update", err)

    def test_no_notice_when_up_to_date(self):
        with mock.patch.object(cli, "_read_cache", return_value={"latest": __version__}):
            _, _, err = run_cli([])
        self.assertNotIn("New mukimov version", err)

    def test_help_is_offline(self):
        with mock.patch.object(cli, "get_latest_version") as fetch:
            for args in ([], ["--help"], ["unknown"]):
                run_cli(args)
        fetch.assert_not_called()


class TestUnknown(unittest.TestCase):
    def test_unknown_command_exit_2(self):
        with mock.patch.object(cli, "get_latest_version", return_value=__version__):
            code, _, err = run_cli(["frobnicate"])
        self.assertEqual(code, 2)
        self.assertIn("Unknown command", err)


class TestBackwardCompat(unittest.TestCase):
    def test_stars_still_works(self):
        from mukimov import stars

        self.assertTrue(callable(stars))
        with self.assertRaises(ValueError):
            stars("Password: ", "")


if __name__ == "__main__":
    unittest.main()
