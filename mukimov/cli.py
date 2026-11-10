"""Command-line interface for ``mukimov``.

Commands::

    mukimov --version     show the installed version
    mukimov update        upgrade to the latest PyPI release
    mukimov --help        show help
    mukimov doctor        diagnose the installation offline
    mukimov example       open the interactive demo
    python -m mukimov     run the same CLI through Python

Help and diagnostics work offline. Version notices use only cached data.

The library is never upgraded automatically: only ``mukimov update``
runs ``pip install --upgrade`` — with the same Python interpreter that
runs ``mukimov``.
"""

from __future__ import annotations

import subprocess
import sys
import importlib.util
import os
import platform
import shutil
import sysconfig
from pathlib import Path

from .update import (
    UpdateCheckError,
    _read_cache,
    format_notice,
    get_current_version,
    get_latest_version,
    is_newer,
)

__all__ = ["main"]


def _ensure_utf8() -> None:
    """Make stdout/stderr UTF-8 capable (Windows cp1252 can't print ⚠/→/ru)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _print_version() -> int:
    sys.stdout.write(f"mukimov {get_current_version()}\n")
    # Show a pending-update hint from cache only (no network here,
    # so --version stays instant and offline-friendly).
    _maybe_notify()
    return 0


def _print_help() -> int:
    sys.stdout.write(
        "Usage: mukimov [--version] [--help] <command>\n"
        "\n"
        "Commands:\n"
        "  update      Check PyPI and upgrade mukimov to the latest version\n"
        "  doctor      Diagnose Python, dependencies and command availability (offline)\n"
        "  example     Open the interactive demo\n"
        "  startweb    Create a new web project in the current directory\n"
        "\n"
        "Options:\n"
        "  --version   Show the installed mukimov version\n"
        "  -V          Alias for --version\n"
        "  -h, --help  Show this help\n"
        "\n"
        "Examples:\n"
        "  mukimov --version\n"
        "  mukimov update\n"
        "  mukimov doctor\n"
        "  mukimov example\n"
        "  mukimov startweb my_site\n"
        "  python -m mukimov --version\n"
    )
    _maybe_notify()
    return 0


def _maybe_notify() -> None:
    """Show an update notice from disk without contacting PyPI."""
    cached = _read_cache()
    if cached and cached.get("latest"):
        latest = str(cached["latest"])
        if is_newer(latest, get_current_version()):
            sys.stderr.write(format_notice(latest) + "\n")


def _cmd_update() -> int:
    current = get_current_version()
    try:
        latest = get_latest_version(force=True)
    except UpdateCheckError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    if not is_newer(latest, current):
        sys.stdout.write(
            f"Already up to date (обновление не требуется): mukimov {current}\n"
        )
        return 0

    # Upgrade with the SAME interpreter that runs mukimov.
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "mukimov"]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError as exc:
        sys.stderr.write(f"Error: could not run pip ({exc}).\n")
        return 1
    except subprocess.TimeoutExpired:
        sys.stderr.write(
            "Error: pip timed out while upgrading mukimov. "
            "Проверьте подключение к интернету и попробуйте позже.\n"
        )
        return 1
    except Exception as exc:
        sys.stderr.write(f"Error: could not upgrade mukimov ({exc}).\n")
        return 1

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip().splitlines()
        detail = err[-1] if err else "pip failed"
        sys.stderr.write(
            f"Error: could not upgrade mukimov: {detail}\n"
            "Проверьте подключение к интернету и попробуйте позже.\n"
        )
        return 1

    # Re-read the installed version after upgrade.
    new_version = latest
    try:
        from importlib.metadata import version as _dist_version

        new_version = str(_dist_version("mukimov"))
    except Exception:
        pass
    sys.stdout.write(f"Updated mukimov: {current} → {new_version}\n")
    return 0


def _cmd_doctor() -> int:
    """Inspect this interpreter and command lookup without network access."""
    sys.stdout.write(
        "mukimov doctor\n"
        f"Version: {get_current_version()}\n"
        f"Python: {platform.python_version()}\n"
        f"Interpreter: {sys.executable}\n"
        f"Platform: {platform.system()}\n"
        f"Package: {Path(__file__).resolve().parent}\n"
        f"Scripts: {sysconfig.get_path('scripts')}\n"
    )
    problems = False
    for module, label in (
        ("pip", "pip"),
        ("packaging", "packaging"),
        ("dotenv", "python-dotenv"),
        ("markdown_it", "markdown-it-py"),
        ("wcwidth", "wcwidth"),
        ("jinja2", "Jinja2"),
    ):
        available = importlib.util.find_spec(module) is not None
        if available:
            status = "OK"
        else:
            status = "MISSING"
            problems = True
        sys.stdout.write(f"{label}: {status}\n")
    command = shutil.which("mukimov")
    if command:
        sys.stdout.write(f"Command in PATH: {command}\n")
        expected = Path(sysconfig.get_path("scripts")) / ("mukimov.exe" if os.name == "nt" else "mukimov")
        if expected.is_file() and Path(command).resolve() != expected.resolve():
            problems = True
            sys.stdout.write("WARNING: PATH selects a launcher outside this interpreter's Scripts directory.\n")
    else:
        problems = True
        sys.stdout.write("Command in PATH: MISSING\nAdd the Scripts directory to PATH or activate your virtual environment.\n")
    sys.stdout.write("Run with this interpreter:\n")
    sys.stdout.write(f'  "{sys.executable}" -m mukimov --version\n')
    if os.name == "nt":
        sys.stdout.write(f'PowerShell:\n  & "{sys.executable}" -m mukimov --version\n')
    sys.stdout.write("Result: " + ("issues found\n" if problems else "OK\n"))
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point (``mukimov`` console script)."""
    _ensure_utf8()
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        _print_help()
        return 0
    if args in (["--version"], ["-V"]):
        return _print_version()
    if args in (["-h"], ["--help"], ["help"]):
        return _print_help()
    if args == ["update"]:
        return _cmd_update()
    if args == ["doctor"]:
        return _cmd_doctor()
    if args == ["example"]:
        from ._example import main as run_example

        run_example()
        return 0
    if args[0] == "startweb":
        from ._startweb import main as startweb

        return startweb(args[1:])
    sys.stderr.write(f"Unknown command: {' '.join(args)}\n")
    _print_help()
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
