"""Красивые ANSI-цвета терминала для ``mukimov``.

Использование::

    from mukimov.color import red, green, blue

    username = input(red("Username: "))
    password = stars(green("Password: "))

    print(red("Error"))
    print(green("Success"))

Каждая функция принимает только ``str`` и возвращает цветную строку
(сама ``print()`` не вызывается). После текста цвет всегда сбрасывается
через ANSI RESET (``\\x1b[0m``), поэтому функции безопасно использовать
в ``input()``, ``print()`` и ``stars()``.

Только стандартная библиотека, без сторонних зависимостей.
Цвета подобраны яркими и читаемыми в Windows Terminal, PowerShell и Linux.
"""

from __future__ import annotations

__all__ = [
    "red",
    "green",
    "blue",
    "yellow",
    "orange",
    "purple",
    "pink",
    "cyan",
    "lime",
    "gray",
    "white",
    "gold",
]

RESET = "\x1b[0m"

_COLORS: dict[str, str] = {
    "red": "\x1b[91m",  # bright red — читаемый красный
    "green": "\x1b[92m",  # bright green
    "blue": "\x1b[94m",  # bright blue (тёмно-синий 34 плохо читается)
    "yellow": "\x1b[93m",  # bright yellow
    "orange": "\x1b[38;5;208m",  # 256-color orange
    "purple": "\x1b[95m",  # bright magenta (purple)
    "pink": "\x1b[38;5;205m",  # 256-color pink
    "cyan": "\x1b[96m",  # bright cyan
    "lime": "\x1b[38;5;118m",  # 256-color lime green
    "gray": "\x1b[90m",  # bright black (gray)
    "white": "\x1b[97m",  # bright white
    "gold": "\x1b[38;5;220m",  # 256-color gold
}


def _colorize(text: str, code: str, func_name: str) -> str:
    """Обернуть ``text`` в ANSI-код ``code`` + RESET с валидацией."""
    if not isinstance(text, str):
        raise TypeError(f"{func_name}() expected str, got {type(text).__name__}")
    if text.strip() == "":
        raise ValueError(f"{func_name}() text cannot be empty")
    return f"{code}{text}{RESET}"


def red(text: str) -> str:
    """Окрасить текст в красный."""
    return _colorize(text, _COLORS["red"], "red")


def green(text: str) -> str:
    """Окрасить текст в зелёный."""
    return _colorize(text, _COLORS["green"], "green")


def blue(text: str) -> str:
    """Окрасить текст в синий."""
    return _colorize(text, _COLORS["blue"], "blue")


def yellow(text: str) -> str:
    """Окрасить текст в жёлтый."""
    return _colorize(text, _COLORS["yellow"], "yellow")


def orange(text: str) -> str:
    """Окрасить текст в оранжевый."""
    return _colorize(text, _COLORS["orange"], "orange")


def purple(text: str) -> str:
    """Окрасить текст в фиолетовый."""
    return _colorize(text, _COLORS["purple"], "purple")


def pink(text: str) -> str:
    """Окрасить текст в розовый."""
    return _colorize(text, _COLORS["pink"], "pink")


def cyan(text: str) -> str:
    """Окрасить текст в голубой (cyan)."""
    return _colorize(text, _COLORS["cyan"], "cyan")


def lime(text: str) -> str:
    """Окрасить текст в лаймовый (светло-зелёный)."""
    return _colorize(text, _COLORS["lime"], "lime")


def gray(text: str) -> str:
    """Окрасить текст в серый."""
    return _colorize(text, _COLORS["gray"], "gray")


def white(text: str) -> str:
    """Окрасить текст в белый."""
    return _colorize(text, _COLORS["white"], "white")


def gold(text: str) -> str:
    """Окрасить текст в золотой."""
    return _colorize(text, _COLORS["gold"], "gold")
