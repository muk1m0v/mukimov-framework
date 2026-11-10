"""Tests for mukimov core logic (no real terminal needed)."""

import inspect
import io
import sys
import unittest
from contextlib import nullcontext
from unittest import mock

from mukimov import stars
from mukimov._windows_console import _characters
from mukimov.stars import (
    _process_keystrokes,
    _stars_windows,
    _validate_mask,
    _validate_prompt,
)


class TestProcessKeystrokes(unittest.TestCase):
    def test_simple_input_enter(self):
        self.assertEqual(_process_keystrokes(list("12345678") + ["\r"]), "12345678")
        self.assertEqual(_process_keystrokes(list("abc") + ["\n"]), "abc")

    def test_backspace_bs(self):
        self.assertEqual(_process_keystrokes(["a", "b", "\x08", "c", "\r"]), "ac")

    def test_backspace_del(self):
        self.assertEqual(_process_keystrokes(["a", "b", "\x7f", "c", "\r"]), "ac")

    def test_backspace_on_empty_ignored(self):
        self.assertEqual(_process_keystrokes(["\x08", "\x7f", "a", "\r"]), "a")

    def test_multiple_backspaces(self):
        self.assertEqual(_process_keystrokes(list("abcd") + ["\x08", "\x08", "\r"]), "ab")

    def test_ctrl_c_raises(self):
        with self.assertRaises(KeyboardInterrupt):
            _process_keystrokes(["a", "\x03"])

    def test_ctrl_d_on_empty_raises_eof(self):
        with self.assertRaises(EOFError):
            _process_keystrokes(["\x04"])

    def test_ctrl_d_with_content_ignored(self):
        self.assertEqual(_process_keystrokes(["a", "\x04", "b", "\r"]), "ab")

    def test_control_chars_ignored(self):
        self.assertEqual(_process_keystrokes(["a", "\x00", "\x1b", "b", "\r"]), "ab")

    def test_unicode(self):
        self.assertEqual(_process_keystrokes(list("пароль") + ["\r"]), "пароль")


class TestApi(unittest.TestCase):
    def test_stars_importable_and_callable(self):
        self.assertTrue(callable(stars))

    def test_signature_defaults(self):
        sig = inspect.signature(stars)
        params = sig.parameters
        self.assertEqual(list(params), ["prompt", "mask"])
        self.assertEqual(params["prompt"].default, "Password: ")
        self.assertEqual(params["mask"].default, "*")

    def test_validate_mask_ok(self):
        self.assertEqual(_validate_mask("*"), "*")
        self.assertEqual(_validate_mask("#"), "#")

    def test_validate_mask_bad(self):
        with self.assertRaisesRegex(ValueError, "Допускается только 1 символ"):
            _validate_mask("**")
        with self.assertRaisesRegex(ValueError, "пустой"):
            _validate_mask("")
        with self.assertRaisesRegex(TypeError, "должен быть строкой"):
            _validate_mask(123)  # type: ignore[arg-type]


class TestMask(unittest.TestCase):
    def test_default_star(self):
        self.assertEqual(_validate_mask("*"), "*")

    def test_slash(self):
        self.assertEqual(_validate_mask("/"), "/")

    def test_hash(self):
        self.assertEqual(_validate_mask("#"), "#")

    def test_unicode_bullet(self):
        self.assertEqual(_validate_mask("•"), "•")

    def test_empty_raises(self):
        with self.assertRaisesRegex(ValueError, "mask='' пустой"):
            _validate_mask("")

    def test_two_chars_raises(self):
        with self.assertRaisesRegex(ValueError, "2 символа"):
            _validate_mask("/*")
        with self.assertRaisesRegex(ValueError, "2 символа"):
            _validate_mask("**")

    def test_word_raises(self):
        with self.assertRaisesRegex(ValueError, "5 символов"):
            _validate_mask("hello")

    def test_stars_rejects_bad_mask(self):
        # Validation happens before any terminal access.
        with self.assertRaisesRegex(ValueError, "пустой"):
            stars("Password: ", "")
        with self.assertRaisesRegex(ValueError, "2 символа"):
            stars("Password: ", "/*")

    def test_backspace_with_custom_mask(self):
        # Buffer logic is mask-independent: result is the raw password.
        self.assertEqual(_process_keystrokes(["1", "2", "\x08", "3", "\r"]), "13")


class TestWindowsEcho(unittest.TestCase):
    def _run(self, keys, prompt="Password: ", mask="*"):
        out = io.StringIO()
        with mock.patch("mukimov.stars.console_keys", return_value=nullcontext(iter(keys))):
            with mock.patch.object(sys, "stdout", out):
                result = _stars_windows(prompt, mask)
        return result, out.getvalue()

    def test_echo_star(self):
        result, shown = self._run(list("12345") + ["\r"])
        self.assertEqual(result, "12345")
        self.assertEqual(shown, "Password: *****\n")

    def test_echo_slash(self):
        result, shown = self._run(list("12345") + ["\r"], mask="/")
        self.assertEqual(result, "12345")
        self.assertEqual(shown, "Password: /////\n")

    def test_echo_hash(self):
        result, shown = self._run(list("hello") + ["\r"], prompt="Secret: ", mask="#")
        self.assertEqual(result, "hello")
        self.assertEqual(shown, "Secret: #####\n")

    def test_echo_unicode_mask(self):
        result, shown = self._run(list("ab") + ["\r"], mask="•")
        self.assertEqual(result, "ab")
        self.assertEqual(shown, "Password: ••\n")

    def test_backspace_custom_mask(self):
        result, shown = self._run(["1", "2", "\x08", "3", "\r"], mask="#")
        self.assertEqual(result, "13")
        self.assertEqual(shown, "Password: ##\b \b#\n")

    def test_accented_character_is_not_a_special_key_prefix(self):
        records = [(ord("a"), 1), (0xe0, 1), (ord("b"), 1), (13, 1)]
        result, shown = self._run(_characters(records))
        self.assertEqual(result, "aàb")
        self.assertEqual(shown, "Password: ***\n")

    def test_windows_utf16_surrogate_pair_counts_as_one_character(self):
        result, shown = self._run(_characters([(0xd83d, 1), (0xde00, 1), (13, 1)]))
        self.assertEqual(result, "😀")
        self.assertEqual(shown, "Password: *\n")


class TestErrors(unittest.TestCase):
    """Точные русскоязычные сообщения для всех случаев из ТЗ."""

    def test_empty_mask_exact(self):
        with self.assertRaises(ValueError) as cm:
            stars("Password: ", "")
        self.assertEqual(
            str(cm.exception),
            "Параметр mask='' пустой. Укажите ровно 1 символ для маскировки.\n"
            'Пример: stars("Password: ", "*")',
        )

    def test_double_slash_exact(self):
        with self.assertRaises(ValueError) as cm:
            stars("Password: ", "//")
        self.assertEqual(
            str(cm.exception),
            "Параметр mask='//' содержит 2 символа. Допускается только 1 символ.\n"
            'Пример: stars("Password: ", "*")',
        )

    def test_slash_star_count(self):
        with self.assertRaises(ValueError) as cm:
            stars("Password: ", "/*")
        msg = str(cm.exception)
        self.assertIn("mask='/*'", msg)
        self.assertIn("2 символа", msg)
        self.assertIn("Допускается только 1 символ", msg)
        self.assertIn("Пример", msg)

    def test_hello_count_not_hardcoded(self):
        with self.assertRaises(ValueError) as cm:
            stars("Password: ", "hello")
        self.assertEqual(
            str(cm.exception),
            "Параметр mask='hello' содержит 5 символов. Допускается только 1 символ.\n"
            'Пример: stars("Password: ", "*")',
        )

    def test_mask_int_exact(self):
        with self.assertRaises(TypeError) as cm:
            stars("Password: ", 123)
        self.assertEqual(
            str(cm.exception),
            "Параметр mask должен быть строкой (str), но получен int: 123.\n"
            'Пример: stars("Password: ", "*")',
        )

    def test_mask_none(self):
        with self.assertRaises(TypeError) as cm:
            stars("Password: ", None)
        self.assertIn("NoneType", str(cm.exception))
        self.assertIn("должен быть строкой", str(cm.exception))

    def test_mask_bool(self):
        with self.assertRaises(TypeError) as cm:
            stars("Password: ", True)
        self.assertIn("bool", str(cm.exception))

    def test_mask_list(self):
        with self.assertRaises(TypeError) as cm:
            stars("Password: ", [])
        msg = str(cm.exception)
        self.assertIn("list", msg)
        self.assertIn("[]", msg)

    def test_mask_dict(self):
        with self.assertRaises(TypeError) as cm:
            stars("Password: ", {})
        self.assertIn("dict", str(cm.exception))

    def test_prompt_int_exact(self):
        with self.assertRaises(TypeError) as cm:
            stars(123)
        self.assertEqual(
            str(cm.exception),
            "Параметр prompt должен быть строкой (str), но получен int: 123.\n"
            'Пример: stars("Password: ")',
        )

    def test_prompt_none(self):
        with self.assertRaises(TypeError) as cm:
            stars(None)
        msg = str(cm.exception)
        self.assertIn("prompt", msg)
        self.assertIn("NoneType", msg)

    def test_spaces_shown_via_repr(self):
        with self.assertRaises(ValueError) as cm:
            stars("Password: ", "  ")
        self.assertIn("mask='  '", str(cm.exception))

    def test_password_never_in_errors(self):
        # Валидаторы получают только конфигурацию (prompt/mask),
        # введённый пароль туда попасть не может.
        self.assertEqual(list(inspect.signature(_validate_mask).parameters), ["mask"])
        self.assertEqual(list(inspect.signature(_validate_prompt).parameters), ["prompt"])


if __name__ == "__main__":
    unittest.main()
