"""Restart the development app in a fresh Python process after source edits."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import __main__
import os
import subprocess
import sys
import time

WORKER_ENV = "MUKIMOV_WEB_RELOAD_WORKER"
BIND_FAILED = 98
_EXCLUDED_DIRS = {"__pycache__", "build", "dist", "node_modules", "venv"}


def _source_snapshot(root: Path, entry: Path) -> dict[Path, tuple[int, int]]:
    files = {entry}
    for base, dirs, names in os.walk(root):
        dirs[:] = [name for name in dirs
                   if not name.startswith(".") and name not in _EXCLUDED_DIRS
                   and not Path(base, name, "pyvenv.cfg").is_file()]
        files.update(Path(base, name) for name in names if name.endswith(".py"))

    snapshot = {}
    for path in files:
        try:
            stat = path.stat()
        except OSError:
            continue
        snapshot[path] = (stat.st_mtime_ns, stat.st_size)
    return snapshot


def _stop(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def supervise(root: Path) -> bool:
    """Run the reloader for script and module entry points."""
    filename = getattr(__main__, "__file__", None)
    if os.environ.get(WORKER_ENV) == "1" or not filename or filename.startswith("<"):
        return False

    entry = Path(filename).resolve()
    original = getattr(sys, "orig_argv", None)
    spec = getattr(__main__, "__spec__", None)
    if original:
        arguments = original[1:]
    elif spec is not None:
        arguments = ["-m", spec.name, *sys.argv[1:]]
    else:
        arguments = [str(entry), *sys.argv[1:]]
    environment = dict(os.environ, **{WORKER_ENV: "1"})

    try:
        with TemporaryDirectory() as bytecode_cache:
            # Avoid reusing timestamp-based bytecode after rapid, same-size edits.
            command = [sys.executable, "-B", "-X", f"pycache_prefix={bytecode_cache}", *arguments]
            while True:
                snapshot = _source_snapshot(root, entry)
                process = subprocess.Popen(command, env=environment)
                try:
                    while True:
                        time.sleep(0.35)
                        if _source_snapshot(root, entry) != snapshot:
                            print("Код изменился, перезапускаю сервер…", flush=True)
                            break
                        status = process.poll()
                        if status == BIND_FAILED:
                            raise SystemExit(1)
                        if status == 0:
                            return True
                        # Keep watching after a syntax error so the next save can recover.
                finally:
                    _stop(process)
    except KeyboardInterrupt:
        return True
