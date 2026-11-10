"""Typed environment settings with explicit, secret-safe .env loading."""

from __future__ import annotations

import builtins
import os
import re
from pathlib import Path
from threading import RLock

__all__ = ["load", "boolean", "integer", "string", "list", "check", "required", "EnvError"]

_MISSING = object()
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_loaded_path = None
_file_names = ()
_load_lock = RLock()


class EnvError(ValueError):
    """Invalid or missing configuration; messages never contain values."""


def _validate_name(name):
    if not isinstance(name, str):
        raise TypeError("Имя переменной должно быть строкой (str).")
    if not _NAME.fullmatch(name):
        raise ValueError("Имя переменной должно содержать буквы, цифры и подчёркивания и не начинаться с цифры.")
    return name


def load(path=".env", *, override=False):
    """Load a UTF-8 dotenv file; existing environment values win by default.

    Loading is explicit. No variable interpolation is performed. Returns
    the names found in the file, never their values. An invalid file is
    rejected before any environment variables are changed.
    """
    global _loaded_path, _file_names
    if type(override) is not bool:
        raise TypeError("Параметр override должен быть bool.")
    try:
        from dotenv.parser import parse_stream
    except ModuleNotFoundError as exc:
        if exc.name != "dotenv":
            raise
        raise ImportError("env.load() requires python-dotenv. Run: python -m pip install --upgrade mukimov") from exc

    file_path = Path(path)
    values = {}
    with file_path.open(encoding="utf-8-sig") as stream:
        for binding in parse_stream(stream):
            if binding.error:
                raise EnvError("Ошибка синтаксиса .env в строке {}. Ожидается ИМЯ=значение.".format(binding.original.line))
            if binding.key is None:
                continue
            if not _NAME.fullmatch(binding.key):
                raise EnvError("Некорректное имя переменной в .env в строке {}.".format(binding.original.line))
            if binding.value is not None and "\x00" in binding.value:
                raise EnvError("Недопустимый нулевой символ в .env в строке {}.".format(binding.original.line))
            values[binding.key] = binding.value if binding.value is not None else ""
    with _load_lock:
        applied = []
        try:
            for name, value in values.items():
                previous = os.environ.get(name, _MISSING)
                if override or previous is _MISSING:
                    os.environ[name] = value
                    applied.append((name, previous))
        except (OSError, ValueError):
            failed_name = name
            for name, previous in reversed(applied):
                if previous is _MISSING:
                    del os.environ[name]
                else:
                    os.environ[name] = previous
            raise EnvError(f"Не удалось записать переменную {failed_name} из .env.") from None
        _loaded_path = file_path
        _file_names = tuple(values)
        return _file_names


def _missing_error(name):
    if _loaded_path is not None:
        if name in _file_names:
            message = "Переменная {} имеет пустое значение!".format(name)
        else:
            message = "Переменная {} в .env отсутствует!".format(name)
        listing = "\n".join(_file_names) if _file_names else "(нет переменных)"
        return EnvError(message + "\nПеременные в .env:\n" + listing)
    return EnvError("Переменная {} в окружении отсутствует или пуста! Для загрузки .env вызовите env.load(\".env\").".format(name))


def required(name: str) -> str:
    """Return a nonblank string or raise EnvError with names only."""
    _validate_name(name)
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise _missing_error(name)
    return value


def boolean(name: str, default=_MISSING) -> bool:
    """Read true/false, 1/0, yes/no or on/off (case insensitive)."""
    _validate_name(name)
    if default is not _MISSING and type(default) is not bool:
        raise TypeError("Параметр default для env.boolean() должен быть bool.")
    if name not in os.environ and default is not _MISSING:
        return default
    value = required(name).strip().lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    raise EnvError("Переменная {} должна содержать true/false, 1/0, yes/no или on/off.".format(name))


def integer(name: str, default=_MISSING, *, min=None, max=None) -> int:
    """Read an integer with inclusive bounds, including for the default."""
    _validate_name(name)
    if default is not _MISSING and type(default) is not int:
        raise TypeError("Параметр default для env.integer() должен быть int.")
    for bound_name, bound in (("min", min), ("max", max)):
        if bound is not None and type(bound) is not int:
            raise TypeError("Параметр {} для env.integer() должен быть int или None.".format(bound_name))
    if min is not None and max is not None and min > max:
        raise ValueError("Параметр min не должен превышать max.")
    if name not in os.environ and default is not _MISSING:
        result = default
    else:
        value = required(name).strip()
        if not re.fullmatch(r"[+-]?[0-9]+", value):
            raise EnvError("Переменная {} должна содержать целое число.".format(name))
        try:
            result = int(value)
        except ValueError:
            raise EnvError("Переменная {} должна содержать допустимое целое число.".format(name)) from None
    if min is not None and result < min:
        raise EnvError("Переменная {} должна быть не меньше {}.".format(name, min))
    if max is not None and result > max:
        raise EnvError("Переменная {} должна быть не больше {}.".format(name, max))
    return result


def string(name: str, default=_MISSING) -> str:
    """Read a nonblank string unchanged, or use an absent-value default."""
    _validate_name(name)
    if default is not _MISSING and not isinstance(default, str):
        raise TypeError("Параметр default для env.string() должен быть str.")
    if name not in os.environ and default is not _MISSING:
        return default
    return required(name)


def list(name: str, default=_MISSING, *, separator=",") -> builtins.list[str]:
    """Split a setting, trim items and omit empty items; copy defaults."""
    _validate_name(name)
    if not isinstance(separator, str):
        raise TypeError("Параметр separator для env.list() должен быть str.")
    if not separator:
        raise ValueError("Параметр separator не должен быть пустым.")
    if default is not _MISSING:
        if not isinstance(default, builtins.list) or not all(isinstance(item, str) for item in default):
            raise TypeError("Параметр default для env.list() должен быть списком строк.")
    if name not in os.environ and default is not _MISSING:
        return default.copy()
    return [item.strip() for item in required(name).split(separator) if item.strip()]


def check(names) -> None:
    """Report all missing/blank required names together, never values."""
    if isinstance(names, (str, bytes)):
        raise TypeError("Параметр names для env.check() должен быть коллекцией имён, а не строкой.")
    try:
        requested = builtins.list(names)
    except TypeError:
        raise TypeError("Параметр names для env.check() должен быть коллекцией имён.") from None
    for name in requested:
        _validate_name(name)
    missing = [name for name in dict.fromkeys(requested)
               if name not in os.environ or not os.environ[name].strip()]
    if missing:
        message = "Обязательные переменные отсутствуют или пусты:\n" + "\n".join(missing)
        if _loaded_path is not None:
            message += "\nПеременные в .env:\n" + ("\n".join(_file_names) or "(нет переменных)")
        raise EnvError(message)
