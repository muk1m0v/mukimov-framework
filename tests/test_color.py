"""Tests for mukimov.color (12 ANSI colors)."""

import unittest
from unittest import mock

import mukimov.color as color_mod
from mukimov.color import (
    blue,
    cyan,
    gold,
    gray,
    green,
    lime,
    orange,
    pink,
    purple,
    red,
    white,
    yellow,
)

ALL_FUNCS = {
    "red": red,
    "green": green,
    "blue": blue,
    "yellow": yellow,
    "orange": orange,
    "purple": purple,
    "pink": pink,
    "cyan": cyan,
    "lime": lime,
    "gray": gray,
    "white": white,
    "gold": gold,
}

EXPECTED_CODES = {
    "red": "\x1b[91m",
    "green": "\x1b[92m",
    "blue": "\x1b[94m",
    "yellow": "\x1b[93m",
    "orange": "\x1b[38;5;208m",
    "purple": "\x1b[95m",
    "pink": "\x1b[38;5;205m",
    "cyan": "\x1b[96m",
    "lime": "\x1b[38;5;118m",
    "gray": "\x1b[90m",
    "white": "\x1b[97m",
    "gold": "\x1b[38;5;220m",
}

RESET = "\x1b[0m"


class TestExports(unittest.TestCase):
    def test_all_12_exported(self):
        for name in ALL_FUNCS:
            self.assertIn(name, color_mod.__all__)
            self.assertTrue(callable(getattr(color_mod, name)))
        self.assertEqual(len(color_mod.__all__), 12)


class TestColorOutput(unittest.TestCase):
    def test_ansi_code_and_reset(self):
        for name, func in ALL_FUNCS.items():
            with self.subTest(color=name):
                result = func("Hello")
                self.assertTrue(result.startswith(EXPECTED_CODES[name]))
                self.assertTrue(result.endswith(RESET))
                self.assertEqual(result, f"{EXPECTED_CODES[name]}Hello{RESET}")

    def test_original_text_preserved(self):
        for name, func in ALL_FUNCS.items():
            with self.subTest(color=name):
                self.assertIn("Hello World", func("Hello World"))
                # Исходная строка сохраняется без strip()
                self.assertEqual(func("Username: "), f"{EXPECTED_CODES[name]}Username: {RESET}")

    def test_reset_at_end(self):
        for name, func in ALL_FUNCS.items():
            with self.subTest(color=name):
                result = func("text")
                self.assertEqual(result[-len(RESET):], RESET)
                # RESET только в конце (один раз после текста)
                self.assertEqual(result.count(RESET), 1)

    def test_returns_str_not_print(self):
        for name, func in ALL_FUNCS.items():
            with self.subTest(color=name):
                with mock.patch("builtins.print") as mprint:
                    result = func("Hi there")
                    self.assertIsInstance(result, str)
                    mprint.assert_not_called()

    def test_username_prompt_ok(self):
        for name, func in ALL_FUNCS.items():
            with self.subTest(color=name):
                result = func("Username: ")
                self.assertIn("Username: ", result)


class TestTypeErrors(unittest.TestCase):
    def test_int_none_bool_list_dict(self):
        bad_values = [(123, "int"), (None, "NoneType"), (True, "bool"), ([], "list"), ({}, "dict")]
        for name, func in ALL_FUNCS.items():
            for value, type_name in bad_values:
                with self.subTest(color=name, value=repr(value)):
                    with self.assertRaises(TypeError) as cm:
                        func(value)  # type: ignore[arg-type]
                    self.assertEqual(str(cm.exception), f"{name}() expected str, got {type_name}")

    def test_no_auto_str_conversion(self):
        with self.assertRaises(TypeError):
            red(123)  # type: ignore[arg-type]
        # Убеждаемся, что "123" как строка — это другой случай (валидный)
        self.assertIn("123", red("123"))


class TestEmptyErrors(unittest.TestCase):
    def test_empty_and_whitespace(self):
        bad = ["", "   ", "\t", "\n", " \t\n "]
        for name, func in ALL_FUNCS.items():
            for value in bad:
                with self.subTest(color=name, value=repr(value)):
                    with self.assertRaises(ValueError) as cm:
                        func(value)
                    self.assertEqual(str(cm.exception), f"{name}() text cannot be empty")


class TestCompatibility(unittest.TestCase):
    def test_input_compatibility(self):
        for name, func in ALL_FUNCS.items():
            with self.subTest(color=name):
                prompt = func("Username: ")
                with mock.patch("builtins.input", return_value="Mukimov") as minput:
                    self.assertEqual(input(prompt), "Mukimov")
                    minput.assert_called_once_with(prompt)

    def test_stars_compatibility(self):
        from mukimov import stars

        with mock.patch("mukimov.stars.stars", return_value="secret") as mstars:
            result = mstars(green("Password: "))
            self.assertEqual(result, "secret")
            called_prompt = mstars.call_args[0][0]
            self.assertTrue(called_prompt.startswith(EXPECTED_CODES["green"]))
            self.assertTrue(called_prompt.endswith(RESET))
        # stars callable из пакета
        self.assertTrue(callable(stars))

    def test_print_compatibility(self):
        with mock.patch("builtins.print") as mprint:
            print(red("Error"))
            print(green("Success"))
            print(blue("Information"))
            self.assertEqual(mprint.call_count, 3)


if __name__ == "__main__":
    unittest.main()
