"""Tests for mukimov.update (PyPI check with 24h cache, no auto-update)."""

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import mukimov
from mukimov import update as upd


class TestVersion(unittest.TestCase):
    def test_pyproject_version_matches(self):
        text = Path(__file__).resolve().parent.parent.joinpath("pyproject.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn(f'version = "{mukimov.__version__}"', text.splitlines())

    def test_console_script_entry_point(self):
        text = Path(__file__).resolve().parent.parent.joinpath("pyproject.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn("[project.scripts]", text)
        self.assertIn('mukimov = "mukimov.cli:main"', text)


class TestIsNewer(unittest.TestCase):
    def test_newer(self):
        self.assertTrue(upd.is_newer("0.2.0", "0.1.6"))
        self.assertTrue(upd.is_newer("0.2.1", "0.2.0"))
        self.assertTrue(upd.is_newer("1.0.0", "0.9.9"))

    def test_pep_440_versions(self):
        self.assertFalse(upd.is_newer("0.2.1rc1", "0.2.1"))
        self.assertTrue(upd.is_newer("0.2.1", "0.2.1rc1"))
        self.assertFalse(upd.is_newer("invalid", "0.2.1"))

    def test_not_newer(self):
        self.assertFalse(upd.is_newer("0.2.0", "0.2.0"))
        self.assertFalse(upd.is_newer("0.1.6", "0.2.0"))


class TestNotice(unittest.TestCase):
    def test_exact_format(self):
        self.assertEqual(
            upd.format_notice("0.2.0"),
            "⚠ New mukimov version available: 0.2.0\nRun: mukimov update",
        )


class TestCache(unittest.TestCase):
    def test_write_and_fresh_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "update_check.json"
            upd._write_cache("0.2.0", p)
            data = upd._read_cache(p)
            self.assertIsNotNone(data)
            self.assertEqual(data["latest"], "0.2.0")
            self.assertTrue(upd._is_fresh(data))

    def test_stale_after_24h(self):
        old = {"latest": "0.1.6", "checked_at": time.time() - 25 * 3600}
        self.assertFalse(upd._is_fresh(old))
        fresh = {"latest": "0.1.6", "checked_at": time.time()}
        self.assertTrue(upd._is_fresh(fresh))

    def test_corrupt_cache_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "update_check.json"
            p.write_text("not-json{{", encoding="utf-8")
            self.assertIsNone(upd._read_cache(p))

    def test_fresh_cache_avoids_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "update_check.json"
            upd._write_cache("0.2.0", p)
            with mock.patch.object(
                upd, "fetch_latest_version", side_effect=AssertionError("no network!")
            ):
                self.assertEqual(upd.get_latest_version(force=False, path=p), "0.2.0")

    def test_stale_cache_triggers_fetch_and_rewrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "update_check.json"
            p.write_text(
                json.dumps({"latest": "0.1.0", "checked_at": time.time() - 30 * 3600}),
                encoding="utf-8",
            )
            with mock.patch.object(upd, "fetch_latest_version", return_value="0.2.0"):
                self.assertEqual(upd.get_latest_version(force=False, path=p), "0.2.0")
            self.assertEqual(upd._read_cache(p)["latest"], "0.2.0")

    def test_force_ignores_fresh_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "update_check.json"
            upd._write_cache("0.1.0", p)
            with mock.patch.object(upd, "fetch_latest_version", return_value="0.2.0"):
                self.assertEqual(upd.get_latest_version(force=True, path=p), "0.2.0")

    def test_fetch_failure_falls_back_to_stale_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "update_check.json"
            p.write_text(
                json.dumps({"latest": "0.1.5", "checked_at": time.time() - 30 * 3600}),
                encoding="utf-8",
            )
            with mock.patch.object(
                upd,
                "fetch_latest_version",
                side_effect=upd.UpdateCheckError("offline"),
            ):
                self.assertEqual(upd.get_latest_version(force=False, path=p), "0.1.5")

    def test_fetch_failure_no_cache_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "missing.json"
            with mock.patch.object(
                upd,
                "fetch_latest_version",
                side_effect=upd.UpdateCheckError("offline"),
            ):
                with self.assertRaises(upd.UpdateCheckError):
                    upd.get_latest_version(force=True, path=p)


class TestFetch(unittest.TestCase):
    def test_network_error_becomes_friendly(self):
        with mock.patch.object(
            upd.urllib.request, "urlopen", side_effect=OSError("no route")
        ):
            with self.assertRaises(upd.UpdateCheckError) as cm:
                upd.fetch_latest_version()
            self.assertIn("Could not check for updates", str(cm.exception))

    def test_bad_json_becomes_friendly(self):
        fake = mock.MagicMock()
        fake.read.return_value = b"not json"
        fake.__enter__.return_value = fake
        fake.__exit__.return_value = False
        with mock.patch.object(upd.urllib.request, "urlopen", return_value=fake):
            with self.assertRaises(upd.UpdateCheckError):
                upd.fetch_latest_version()


class TestNoImportSideEffects(unittest.TestCase):
    def test_import_mukimov_does_not_import_update_or_cli(self):
        code = (
            "import sys; import mukimov; "
            "print('mukimov.update' in sys.modules or 'mukimov.cli' in sys.modules)"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, timeout=30
        )
        self.assertEqual(proc.stdout.strip(), "False")

    def test_import_mukimov_does_no_network(self):
        code = "\n".join(
            [
                "import socket, urllib.request",
                "def _blocked(*a, **k):",
                "    raise OSError('blocked')",
                "socket.create_connection = _blocked",
                "urllib.request.urlopen = _blocked",
                "import mukimov",
                "print('OK ' + mukimov.__version__)",
            ]
        )
        proc = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, timeout=30
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn(f"OK {mukimov.__version__}", proc.stdout)


if __name__ == "__main__":
    unittest.main()
