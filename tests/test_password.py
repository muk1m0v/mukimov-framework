import unittest
from unittest.mock import patch

from mukimov.password import hash_password, high, low, medium, verify_password


class TestPassword(unittest.TestCase):
    def test_all_levels_with_unicode_password(self):
        password = "пароль 🔑"
        for level, length in ((low, 118), (medium, 121), (high, 255)):
            with self.subTest(level=level):
                stored = hash_password(password, level=level)
                self.assertEqual(len(stored), length)
                self.assertTrue(stored.isascii())
                self.assertTrue(verify_password(password, stored))
                self.assertFalse(verify_password("wrong password", stored))

    def test_same_password_uses_a_fresh_salt(self):
        first = hash_password("1234ok", level=low)
        second = hash_password("1234ok", level="low")
        self.assertNotEqual(first.split("$")[2], second.split("$")[2])
        self.assertTrue(verify_password("1234ok", second))

    def test_default_and_alias_use_medium(self):
        with patch("mukimov.password.secrets.token_bytes", return_value=bytes(16)):
            default = hash_password("1234ok")
            alias = hash_password("1234ok", level="mediuim")
        self.assertEqual(default.split("$")[1], "medium")
        self.assertEqual(default, alias)

    def test_malformed_hashes_are_rejected_without_deriving_a_key(self):
        stored = hash_password("1234ok", level=low)
        for invalid in ("", stored[:-1], stored + "$extra", "x" * 256,
                        stored.replace("$low$", "$1000000000$"),
                        stored.replace("-v1$", "-v2$"), stored[:-1] + "g"):
            with self.subTest(invalid=invalid), patch("mukimov.password._derive") as derive:
                self.assertFalse(verify_password("1234ok", invalid))
                derive.assert_not_called()

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            hash_password("1234ok", level="fast")
        with self.assertRaises(TypeError):
            hash_password(b"1234ok")
        with self.assertRaises(TypeError):
            hash_password("1234ok", level=1)
        with self.assertRaises(TypeError):
            verify_password("1234ok", None)
