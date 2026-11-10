"""Project paths for Mukimov Web settings."""

from contextvars import ContextVar
from pathlib import Path
from runpy import run_path
import sys

__all__ = ["BASE_DIR"]

_project_root = ContextVar("mukimov_project_root", default=None)


def __getattr__(name):
    if name != "BASE_DIR":
        raise AttributeError(name)
    root = _project_root.get()
    if root is not None:
        return root
    filename = sys._getframe(1).f_globals.get("__file__")
    if not filename:
        return Path.cwd()
    path = Path(filename).resolve()
    if path.name == "conf.py" and path.parent.name == "core":
        return path.parent.parent
    return path.parent


def _load_settings(root):
    for path in (root / "core" / "conf.py", root / "conf.py"):
        if path.is_file():
            token = _project_root.set(root)
            try:
                return run_path(str(path))
            finally:
                _project_root.reset(token)
    return None
