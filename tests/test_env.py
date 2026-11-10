"""Behavior and secret-safe diagnostics for typed environment settings."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mukimov import env


class TestEnv(unittest.TestCase):
    def setUp(self):
        self.environ_patch = patch.dict(os.environ, {}, clear=True)
        self.environ_patch.start()
        self.addCleanup(self.environ_patch.stop)
        self.state_patch = patch.multiple(env, _loaded_path=None, _file_names=())
        self.state_patch.start()
        self.addCleanup(self.state_patch.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / ".env"

    def load(self, content, **kwargs):
        self.path.write_text(content, encoding="utf-8")
        return env.load(self.path, **kwargs)

    def test_missing_variable_lists_only_file_names(self):
        self.load("DB_PASS=very-secret-password\nSUPER_KEY=private-api-key\n")
        with self.assertRaises(env.EnvError) as caught:
            env.required("SECRET_KEY")
        self.assertEqual(str(caught.exception), "Переменная SECRET_KEY в .env отсутствует!\nПеременные в .env:\nDB_PASS\nSUPER_KEY")

    def test_empty_required_lists_names_without_values(self):
        self.load("SECRET_KEY=\nDB_PASS=private-password\n")
        with self.assertRaises(env.EnvError) as caught:
            env.required("SECRET_KEY")
        self.assertIn("пустое значение", str(caught.exception))
        self.assertIn("DB_PASS", str(caught.exception))
        self.assertNotIn("private-password", str(caught.exception))

    def test_empty_file(self):
        self.load("# comment\n")
        with self.assertRaisesRegex(env.EnvError, "нет переменных"):
            env.required("SECRET_KEY")

    def test_system_environment_has_priority(self):
        os.environ["PORT"] = "9000"
        self.load("PORT=8000\n")
        self.assertEqual(env.integer("PORT"), 9000)
        self.load("PORT=8000\n", override=True)
        self.assertEqual(env.integer("PORT"), 8000)

    def test_system_required_need_not_exist_in_file(self):
        os.environ["SECRET_KEY"] = "system-secret"
        self.load("PORT=8000\n")
        self.assertEqual(env.required("SECRET_KEY"), "system-secret")

    def test_boolean_values(self):
        for value in ("true", "TRUE", "1", "yes", "On", " true "):
            with self.subTest(value=value):
                os.environ["DEBUG"] = value
                self.assertIs(env.boolean("DEBUG"), True)
        for value in ("false", "FALSE", "0", "no", "Off", " false "):
            with self.subTest(value=value):
                os.environ["DEBUG"] = value
                self.assertIs(env.boolean("DEBUG"), False)

    def test_defaults_only_for_absent_values(self):
        self.assertIs(env.boolean("DEBUG", default=False), False)
        self.assertEqual(env.integer("PORT", default=8000), 8000)
        os.environ["PORT"] = ""
        with self.assertRaises(env.EnvError):
            env.integer("PORT", default=8000)
        os.environ["DEBUG"] = "secret-invalid-bool"
        with self.assertRaises(env.EnvError) as caught:
            env.boolean("DEBUG", default=False)
        self.assertNotIn("secret-invalid-bool", str(caught.exception))

    def test_integer_values_and_secret_safe_error(self):
        for text, expected in (("8000", 8000), (" -12 ", -12), ("+1", 1), ("0", 0)):
            os.environ["PORT"] = text
            self.assertEqual(env.integer("PORT"), expected)
        invalid_values = ["secret-number", "1.5", "1_000"]
        if hasattr(sys, "get_int_max_str_digits") and sys.get_int_max_str_digits():
            invalid_values.append("9" * (sys.get_int_max_str_digits() + 1))
        for text in invalid_values:
            os.environ["PORT"] = text
            with self.assertRaises(env.EnvError) as caught:
                env.integer("PORT")
            self.assertNotIn(text, str(caught.exception))
            self.assertIsNone(caught.exception.__cause__)

    def test_no_default_means_required(self):
        for getter in (env.required, env.integer, env.boolean):
            with self.subTest(getter=getter), self.assertRaises(env.EnvError):
                getter("MISSING")

    def test_required_preserves_real_value(self):
        os.environ["SECRET_KEY"] = "  secret  "
        self.assertEqual(env.required("SECRET_KEY"), "  secret  ")
        os.environ["SECRET_KEY"] = " \t\n"
        with self.assertRaises(env.EnvError):
            env.required("SECRET_KEY")

    def test_quotes_export_comments_and_no_interpolation(self):
        names = self.load('export TITLE="hello world"\n# comment\nPASS=abc#123\nLITERAL="${PASS}"\nBARE\nUNICODE="пароль"\n')
        self.assertEqual(names, ("TITLE", "PASS", "LITERAL", "BARE", "UNICODE"))
        self.assertEqual(env.required("TITLE"), "hello world")
        self.assertEqual(env.required("PASS"), "abc#123")
        self.assertEqual(env.required("LITERAL"), "${PASS}")
        self.assertEqual(env.required("UNICODE"), "пароль")
        with self.assertRaises(env.EnvError):
            env.required("BARE")

    def test_duplicate_names_and_bom(self):
        names = self.load("\ufeffPORT=1\nPORT=2\n")
        self.assertEqual(names, ("PORT",))
        self.assertEqual(env.integer("PORT"), 2)

    def test_invalid_file_is_atomic_and_secret_safe(self):
        for content in ('VALID=ok\nPASSWORD="never-show-this\n', 'VALID=ok\nbad-name=never-show-this\n', 'VALID=ok\nPASSWORD=never-show-this\x00\n'):
            with self.subTest(content=content):
                with self.assertRaises(env.EnvError) as caught:
                    self.load(content)
                self.assertNotIn("never-show-this", str(caught.exception))
                self.assertNotIn("VALID", os.environ)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            env.load(self.path)

    def test_write_failure_rolls_back_changes_and_preserves_previous_metadata(self):
        class RejectingEnvironment(dict):
            def __setitem__(self, name, value):
                if name == "REJECTED":
                    raise ValueError("secret value")
                super().__setitem__(name, value)

        self.load("EXISTING=original\n")
        environment = RejectingEnvironment(os.environ)
        with patch.object(env.os, "environ", environment):
            with self.assertRaisesRegex(env.EnvError, "REJECTED") as caught:
                self.load("EXISTING=replaced\nADDED=new\nREJECTED=private\n", override=True)
            self.assertNotIn("secret", str(caught.exception))
            self.assertNotIn("private", str(caught.exception))
            self.assertEqual(environment, {"EXISTING": "original"})
            self.assertEqual(env._file_names, ("EXISTING",))

    def test_latest_file_names_replace_previous_listing(self):
        self.load("FIRST=secret\n")
        self.load("SECOND=other-secret\n")
        with self.assertRaises(env.EnvError) as caught:
            env.required("MISSING")
        self.assertIn("SECOND", str(caught.exception))
        self.assertNotIn("FIRST", str(caught.exception))

    def test_names_defaults_and_override_validation(self):
        for getter in (env.required, env.boolean, env.integer):
            with self.assertRaises(TypeError):
                getter(123)
            with self.assertRaises(ValueError):
                getter("invalid\nname")
        with self.assertRaises(TypeError):
            env.boolean("DEBUG", default="false")
        with self.assertRaises(TypeError):
            env.integer("PORT", default=True)
        with self.assertRaises(TypeError):
            env.load(self.path, override=1)


if __name__ == "__main__":
    unittest.main()
