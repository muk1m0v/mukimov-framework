"""Check for new ``mukimov`` releases on PyPI (cached, never automatic).

This module has NO side effects on import: it never touches the network
unless one of the functions below is called explicitly (only the CLI
calls them). Results are cached on disk for 24 hours so repeated CLI
invocations do not hammer PyPI.

Cache location:
  * Windows: ``%LOCALAPPDATA%\\mukimov\\update_check.json``
  * POSIX: ``$XDG_CACHE_HOME/mukimov/update_check.json``
    (defaults to ``~/.cache/mukimov/update_check.json``)
  * Override for tests / custom setups via ``MUKIMOV_CACHE_FILE`` env var.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

from packaging.version import InvalidVersion, Version

__all__ = [
    "UpdateCheckError",
    "CACHE_TTL_SECONDS",
    "PYPI_JSON_URL",
    "UPDATE_NOTICE",
    "get_cache_path",
    "get_current_version",
    "fetch_latest_version",
    "get_latest_version",
    "is_newer",
    "format_notice",
]

CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours
PYPI_JSON_URL = "https://pypi.org/pypi/mukimov/json"

UPDATE_NOTICE = "⚠ New mukimov version available: {latest}\nRun: mukimov update"


class UpdateCheckError(Exception):
    """Friendly, user-facing error for network/PyPI/pip problems."""


def get_cache_path() -> Path:
    """Return the path of the update-check cache file (no I/O)."""
    override = os.environ.get("MUKIMOV_CACHE_FILE")
    if override:
        return Path(override)
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "mukimov" / "update_check.json"
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "mukimov" / "update_check.json"


def get_current_version() -> str:
    """Return the currently installed ``mukimov`` version (never raises)."""
    try:
        from . import __version__ as ver

        return str(ver)
    except Exception:
        pass
    try:
        from importlib.metadata import version as _dist_version

        return str(_dist_version("mukimov"))
    except Exception:
        return "0.0.0"


def is_newer(latest: str, current: str) -> bool:
    """Compare versions according to PEP 440."""
    try:
        return Version(latest) > Version(current)
    except InvalidVersion:
        return False


def format_notice(latest: str) -> str:
    """Render the update notification text for *latest*."""
    return UPDATE_NOTICE.format(latest=latest)


def _read_cache(path: Path | None = None) -> dict | None:
    """Read the cache file; return None on any problem (never raises)."""
    try:
        p = path or get_cache_path()
        if not p.is_file():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        if "latest" not in data or "checked_at" not in data:
            return None
        return data
    except Exception:
        return None


def _write_cache(latest: str, path: Path | None = None) -> None:
    """Write the cache file; silently ignore any I/O problem."""
    try:
        p = path or get_cache_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {"latest": str(latest), "checked_at": time.time()}
        p.write_text(json.dumps(payload), encoding="utf-8")
    except Exception:
        pass


def _is_fresh(data: dict | None, ttl: int = CACHE_TTL_SECONDS) -> bool:
    if not data:
        return False
    try:
        age = time.time() - float(data.get("checked_at", 0))
        return 0 <= age < ttl
    except Exception:
        return False


def fetch_latest_version(timeout: float = 10) -> str:
    """Fetch the latest ``mukimov`` version from PyPI.

    Raises:
        UpdateCheckError: on any network/PyPI/parse problem with a
            human-friendly message (no traceback details leaked).
    """
    try:
        req = urllib.request.Request(
            PYPI_JSON_URL, headers={"User-Agent": "mukimov-update-check"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        version = data.get("info", {}).get("version", "")
        if not version or not isinstance(version, str):
            raise ValueError("bad PyPI response")
        Version(version)
        return version.strip()
    except UpdateCheckError:
        raise
    except Exception as exc:
        kind = type(exc).__name__
        raise UpdateCheckError(
            "Could not check for updates: no connection to PyPI "
            f"({PYPI_JSON_URL}). Проверьте подключение к интернету "
            f"и попробуйте позже. ({kind})"
        ) from exc


def get_latest_version(
    force: bool = False,
    timeout: float = 10,
    path: Path | None = None,
) -> str:
    """Return the latest PyPI version, using the 24h cache when possible.

    * ``force=False``: fresh cache hit returns immediately without network.
    * ``force=True``: always queries PyPI (used by ``mukimov update``).

    On fetch failure with a usable (even stale) cache, the cached value
    is returned instead of raising, so the CLI can still notify.
    If there is no cache at all and the network fails, raises
    :exc:`UpdateCheckError`.

    The cache is updated on every successful fetch.
    """
    cache_path = path or get_cache_path()
    cached = _read_cache(cache_path)
    if not force and _is_fresh(cached):
        return str(cached["latest"])
    try:
        latest = fetch_latest_version(timeout=timeout)
    except UpdateCheckError:
        if not force and cached and cached.get("latest"):
            return str(cached["latest"])
        raise
    _write_cache(latest, cache_path)
    return latest
