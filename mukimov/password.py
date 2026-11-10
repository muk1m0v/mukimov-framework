"""Hash passwords for storage and verify them using PBKDF2-HMAC-SHA256."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from typing import Literal

__all__ = ["hash_password", "verify_password", "low", "medium", "high"]

low: Literal["low"] = "low"
medium: Literal["medium"] = "medium"
high: Literal["high"] = "high"

# Keep the parameters of released formats fixed so stored hashes stay usable.
_FORMAT = "pbkdf2-sha256-v1"
_LEVELS = {
    low: (600_000, 16),
    medium: (900_000, 16),
    high: (1_200_000, 84),  # Format, level, salt and digest total 255 characters.
}
_DIGEST_BYTES = 32
_HEX = re.compile(r"[0-9a-f]+")


def _password_bytes(password: str) -> bytes:
    if not isinstance(password, str):
        raise TypeError("password must be a str")
    return password.encode("utf-8")


def _derive(password: bytes, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password, salt, iterations, dklen=_DIGEST_BYTES)


def hash_password(
    password: str, level: Literal["low", "medium", "high", "mediuim"] = medium
) -> str:
    """Return a versioned hash with a fresh random salt. Defaults to medium.

    ``high`` produces exactly 255 ASCII characters. ``mediuim`` is an alias
    for ``medium``. Save the entire returned string for verification.
    """
    if not isinstance(level, str):
        raise TypeError("level must be a str")
    if level == "mediuim":
        level = medium
    if level not in _LEVELS:
        raise ValueError("level must be 'low', 'medium', or 'high'")

    raw_password = _password_bytes(password)
    iterations, salt_bytes = _LEVELS[level]
    salt = secrets.token_bytes(salt_bytes)
    digest = _derive(raw_password, salt, iterations)
    return f"{_FORMAT}${level}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Check a password against a stored hash. Malformed hashes return False."""
    raw_password = _password_bytes(password)
    if not isinstance(stored_hash, str):
        raise TypeError("stored_hash must be a str")
    if len(stored_hash) > 255:
        return False

    fields = stored_hash.split("$")
    if len(fields) != 4:
        return False
    version, level, salt, digest = fields
    if version != _FORMAT or level not in _LEVELS:
        return False
    iterations, salt_bytes = _LEVELS[level]
    if len(salt) != 2 * salt_bytes or len(digest) != 2 * _DIGEST_BYTES:
        return False
    if not _HEX.fullmatch(salt) or not _HEX.fullmatch(digest):
        return False

    actual = _derive(raw_password, bytes.fromhex(salt), iterations)
    return hmac.compare_digest(actual, bytes.fromhex(digest))
