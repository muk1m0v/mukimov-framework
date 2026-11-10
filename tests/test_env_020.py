"""Configuration behavior added in 0.2.0."""
import os
import unittest
from unittest.mock import patch

from mukimov import env


class TestSettings(unittest.TestCase):
    def setUp(self):
        self.state = patch.multiple(env, _loaded_path=None, _file_names=())
        self.state.start()
        self.addCleanup(self.state.stop)
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_string_default_and_required(self):
        self.assertEqual(env.string("HOST", default="localhost"), "localhost")
        self.assertEqual(env.string("HOST", default=""), "")
        with self.assertRaises(env.EnvError):
            env.string("HOST")
        os.environ["HOST"] = "  example.com  "
        self.assertEqual(env.string("HOST", default="localhost"), "  example.com  ")

    def test_string_empty_is_error_not_default(self):
        os.environ["HOST"] = "   "
        with self.assertRaises(env.EnvError):
            env.string("HOST", default="localhost")

    def test_string_default_type(self):
        for value in (1, False, None, []):
            with self.subTest(value=value), self.assertRaises(TypeError):
                env.string("HOST", default=value)

    def test_lists_trim_and_skip_empty_items(self):
        os.environ["ALLOWED_HOSTS"] = " localhost, example.com, ,127.0.0.1, "
        self.assertEqual(env.list("ALLOWED_HOSTS"), ["localhost", "example.com", "127.0.0.1"])
        os.environ["ALLOWED_HOSTS"] = ",,"
        self.assertEqual(env.list("ALLOWED_HOSTS"), [])

    def test_custom_separator(self):
        os.environ["HOSTS"] = "one; two; three"
        self.assertEqual(env.list("HOSTS", separator=";"), ["one", "two", "three"])

    def test_list_default_is_copied(self):
        default = ["localhost"]
        first = env.list("HOSTS", default=default)
        first.append("another")
        self.assertEqual(default, ["localhost"])
        self.assertEqual(env.list("HOSTS", default=default), ["localhost"])
        self.assertEqual(env.list("HOSTS", default=[]), [])

    def test_empty_list_variable_is_error(self):
        os.environ["HOSTS"] = ""
        with self.assertRaises(env.EnvError):
            env.list("HOSTS", default=[])

    def test_list_default_and_separator_validation(self):
        for value in ("localhost", None, 1, [1], ("localhost",)):
            with self.subTest(value=value), self.assertRaises(TypeError):
                env.list("HOSTS", default=value)
        with self.assertRaises(TypeError):
            env.list("HOSTS", separator=1)
        with self.assertRaises(ValueError):
            env.list("HOSTS", separator="")

    def test_inclusive_integer_bounds(self):
        for value in (1, 65535, 8000):
            os.environ["PORT"] = str(value)
            self.assertEqual(env.integer("PORT", min=1, max=65535), value)
        for value in (0, 65536):
            os.environ["PORT"] = str(value)
            with self.assertRaises(env.EnvError):
                env.integer("PORT", min=1, max=65535)

    def test_integer_bounds_on_default(self):
        self.assertEqual(env.integer("PORT", default=8000, min=1, max=65535), 8000)
        with self.assertRaises(env.EnvError):
            env.integer("PORT", default=0, min=1)
        with self.assertRaises(env.EnvError):
            env.integer("PORT", default=65536, max=65535)

    def test_single_and_equal_bounds(self):
        os.environ["N"] = "-5"
        self.assertEqual(env.integer("N", min=-5, max=-5), -5)
        self.assertEqual(env.integer("N", min=-10), -5)
        self.assertEqual(env.integer("N", max=0), -5)

    def test_bound_validation(self):
        for argument in ("min", "max"):
            for value in (True, "1", 1.5):
                with self.subTest(argument=argument, value=value), self.assertRaises(TypeError):
                    env.integer("N", default=1, **{argument: value})
        with self.assertRaises(ValueError):
            env.integer("N", default=1, min=10, max=1)

    def test_range_error_never_contains_value(self):
        os.environ["NUMBER"] = "123456789"
        with self.assertRaises(env.EnvError) as caught:
            env.integer("NUMBER", max=100)
        self.assertNotIn("123456789", str(caught.exception))

    def test_check_reports_all_missing_and_empty_names(self):
        os.environ["EMPTY"] = "   "
        os.environ["EXISTS"] = "private-value"
        with self.assertRaises(env.EnvError) as caught:
            env.check(["SECRET_KEY", "DB_HOST", "EMPTY", "EXISTS", "DB_HOST"])
        self.assertEqual(str(caught.exception), "Обязательные переменные отсутствуют или пусты:\nSECRET_KEY\nDB_HOST\nEMPTY")

    def test_check_success_and_empty_collection(self):
        os.environ["KEY"] = "secret"
        self.assertIsNone(env.check(["KEY"]))
        self.assertIsNone(env.check([]))
        self.assertIsNone(env.check(iter(["KEY"])))

    def test_check_file_listing_never_includes_values(self):
        with patch.multiple(env, _loaded_path=".env", _file_names=("DB_PASS", "SUPER_KEY")):
            os.environ["DB_PASS"] = "private-password"
            with self.assertRaises(env.EnvError) as caught:
                env.check(["SECRET_KEY", "DB_HOST"])
        self.assertEqual(str(caught.exception), "Обязательные переменные отсутствуют или пусты:\nSECRET_KEY\nDB_HOST\nПеременные в .env:\nDB_PASS\nSUPER_KEY")

    def test_check_names_validation(self):
        for value in ("SECRET_KEY", b"KEY", None, 123):
            with self.subTest(value=value), self.assertRaises(TypeError):
                env.check(value)
        with self.assertRaises(TypeError):
            env.check([1])
        with self.assertRaises(ValueError):
            env.check(["bad-name"])

    def test_new_getters_validate_names(self):
        for getter in (env.string, env.list):
            with self.subTest(getter=getter), self.assertRaises(TypeError):
                getter(1)
            with self.subTest(getter=getter), self.assertRaises(ValueError):
                getter("bad-name")


if __name__ == "__main__":
    unittest.main()
