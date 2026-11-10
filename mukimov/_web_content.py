"""Load static-content directories and HTML aliases from a project's conf.py."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from urllib.parse import quote
import re

ALIAS_PATTERN = r"[\w-]+"
_PREFIX = re.compile(r"/(?:[\w-]+/)*[\w-]+/?")
_CATEGORIES = (
    ("CSS_SETTING", "STYLE_MAIN_PATH", "/content/css/", {".css"}),
    ("JAVASCRIPT_SETTING", "SCRIPT_MAIN_PATH", "/content/js/", {".js", ".mjs"}),
    ("IMAGE_SETTING", "IMAGE_MAIN_PATH", "/content/img/",
     {".apng", ".avif", ".bmp", ".gif", ".ico", ".jpeg", ".jpg", ".png", ".svg", ".tif", ".tiff", ".webp"}),
)


def asset_parts(name: str) -> list[str]:
    parts = name.split("/")
    if any(not part or part.startswith(".") for part in parts) or any(
        char in name for char in ("\\", ":", "\x00")
    ):
        raise ValueError("Invalid asset path.")
    return parts


def load_content(root: Path, settings):
    """Return URL mounts and the optional alias table for the application."""
    mounts = {"/static/": (root / "static", None)}
    if settings is None:
        return mounts, None

    enabled = settings.get("ALL_CONTENT_STATIC", settings.get("ALL_CONTENT", True))
    if type(enabled) is not bool:
        raise ValueError("ALL_CONTENT_STATIC in conf.py must be True or False.")
    aliases = {} if enabled else None
    for setting, path_key, default_prefix, extensions in _CATEGORIES:
        entries = settings.get(setting, {})
        if not isinstance(entries, dict):
            raise ValueError(f"{setting} in conf.py must be a dictionary.")
        prefix = entries.get(path_key, default_prefix)
        if not isinstance(prefix, str) or not _PREFIX.fullmatch(prefix):
            raise ValueError(f"{path_key} in conf.py must be a path such as {default_prefix!r}.")
        prefix = prefix.rstrip("/") + "/"
        if any(prefix.startswith(other) or other.startswith(prefix) for other in mounts):
            raise ValueError(f"{path_key} overlaps another static directory: {prefix}")
        mounts[prefix] = (root.joinpath(*prefix.strip("/").split("/")), extensions)

        if aliases is not None:
            for name, alias in entries.items():
                if name == path_key:
                    continue
                if not isinstance(name, str) or PurePosixPath(name).suffix.lower() not in extensions:
                    raise ValueError(f"{setting} contains an unsupported file: {name!r}")
                asset_parts(name)
                if not isinstance(alias, str) or not re.fullmatch(ALIAS_PATTERN, alias):
                    raise ValueError(f"Invalid alias in {setting}: {alias!r}")
                if alias in aliases:
                    raise ValueError(f"Duplicate content alias: {alias!r}")
                aliases[alias] = quote(prefix + name)
    return mounts, aliases
