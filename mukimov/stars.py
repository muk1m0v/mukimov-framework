"""Core implementation of ``mukimov.stars``.

Cross-platform password prompt that echoes ``*`` for every typed character.
Standard library only.
"""

from __future__ import annotations

import sys

from ._windows_console import console_keys

__all__ = ["stars"]

ENTER_KEYS = ("\r", "\n")
BACKSPACE_KEYS = ("\x08", "\x7f")
INTERRUPT_KEY = "\x03"  # Ctrl+C
EOF_KEY = "\x04"  # Ctrl+D


def _process_keystrokes(keys, echo=None) -> str:
    """Pure, testable core logic: apply keys to a buffer.

    - Normal printable char -> append.
    - Backspace (``\\x08`` / ``\\x7f``) -> pop last char if any.
    - Enter (``\\r`` / ``\\n``) -> stop and return result.
    - Ctrl+C (``\\x03``) -> raise ``KeyboardInterrupt``.
    - Ctrl+D (``\\x04``) on empty buffer -> raise ``EOFError``.
    - Other control chars (ord < 32) -> ignored.
    """
    buf: list[str] = []
    for key in keys:
        if key in ENTER_KEYS:
            break
        if key in BACKSPACE_KEYS:
            if buf:
                buf.pop()
                if echo:
                    echo(False)
            continue
        if key == INTERRUPT_KEY:
            raise KeyboardInterrupt
        if key == EOF_KEY:
            if not buf:
                raise EOFError
            continue
        if len(key) != 1:
            continue
        if ord(key) < 32:
            # Ignore other control chars.
            continue
        buf.append(key)
        if echo:
            echo(True)
    return "".join(buf)


def _plural_ru(n: int, forms: tuple[str, str, str]) -> str:
    """Русское plural-склонение: 1 символ, 2 символа, 5 символов."""
    n10 = n % 10
    n100 = n % 100
    if n10 == 1 and n100 != 11:
        return forms[0]
    if 2 <= n10 <= 4 and not 12 <= n100 <= 14:
        return forms[1]
    return forms[2]


def _validate_prompt(prompt: str) -> str:
    if not isinstance(prompt, str):
        raise TypeError(
            f"Параметр prompt должен быть строкой (str), "
            f"но получен {type(prompt).__name__}: {prompt!r}.\n"
            f'Пример: stars("Password: ")'
        )
    return prompt


def _validate_mask(mask: str) -> str:
    if not isinstance(mask, str):
        raise TypeError(
            f"Параметр mask должен быть строкой (str), "
            f"но получен {type(mask).__name__}: {mask!r}.\n"
            f'Пример: stars("Password: ", "*")'
        )
    if len(mask) == 0:
        raise ValueError(
            f"Параметр mask={mask!r} пустой. "
            f"Укажите ровно 1 символ для маскировки.\n"
            f'Пример: stars("Password: ", "*")'
        )
    if len(mask) != 1:
        word = _plural_ru(len(mask), ("символ", "символа", "символов"))
        raise ValueError(
            f"Параметр mask={mask!r} содержит {len(mask)} {word}. "
            f"Допускается только 1 символ.\n"
            f'Пример: stars("Password: ", "*")'
        )
    return mask


def stars(prompt: str = "Password: ", mask: str = "*") -> str:
    """Read a password, echoing ``mask`` for each character.

    Example:
        >>> from mukimov import stars
        >>> password = stars("Password: ")
        Password: ********
        >>> password = stars("Password: ", "/")
        Password: ////////
        >>> password = stars("Secret: ", "#")
        Secret: #####

    Args:
        prompt: Text shown before input.
        mask: Exactly one character used to echo each typed symbol.
            Defaults to ``"*"``. Raises :exc:`TypeError` if ``prompt``
            or ``mask`` is not a string, and :exc:`ValueError` if
            ``mask`` is not exactly one character. Messages are in
            Russian and never include the typed password.

    Behaviour:
        * Every typed character is immediately shown as ``mask``.
        * Backspace removes the last ``mask`` symbol and char from result.
        * Enter finishes input and prints a newline.
        * The real password is never written to the terminal.
        * Ctrl+C raises ``KeyboardInterrupt``, Ctrl+D on empty input
          raises ``EOFError`` (like ``input()`` / ``getpass()``).

    When stdin is not a TTY, tries :func:`getpass.getpass` and raises
    RuntimeError if echo-free input is unavailable.
    """
    _validate_prompt(prompt)
    _validate_mask(mask)

    if not sys.stdin.isatty():
        import getpass
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            try:
                return getpass.getpass(prompt)
            except getpass.GetPassWarning:
                raise RuntimeError("Password input requires a terminal with echo disabled.") from None

    if sys.platform.startswith("win"):
        return _stars_windows(prompt, mask)
    return _stars_unix(prompt, mask)


def _stars_windows(prompt: str, mask: str) -> str:
    def echo(added):
        print(mask if added else "\b \b", end="", flush=True)

    with console_keys(sys.stdin) as keys:
        print(prompt, end="", flush=True)
        try:
            return _process_keystrokes(keys, echo)
        finally:
            print(flush=True)


def _stars_unix(prompt: str, mask: str) -> str:
    import codecs
    import os
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    sys.stdout.write(prompt)
    sys.stdout.flush()

    old_settings = termios.tcgetattr(fd)
    buf: list[str] = []
    decode = codecs.getincrementaldecoder(sys.stdin.encoding or "utf-8")(
        errors=sys.stdin.errors or "strict"
    )
    escape = ""
    try:
        tty.setraw(fd)
        while True:
            if escape and not select.select([fd], [], [], 0.05)[0]:
                escape = ""
            data = os.read(fd, 1)
            if not data:
                raise EOFError
            key = decode.decode(data)
            if not key:
                continue
            if key == "\x1b":
                escape = key
                continue
            if escape == "\x1b" and key in ("[", "O"):
                escape = key
                continue
            if escape in ("[", "O") and " " <= key <= "~":
                if "@" <= key:
                    escape = ""
                continue
            escape = ""
            if key in ENTER_KEYS:
                break
            if key in BACKSPACE_KEYS:
                if buf:
                    buf.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            if key == INTERRUPT_KEY:
                raise KeyboardInterrupt
            if key == EOF_KEY:
                if not buf:
                    raise EOFError
                continue
            if len(key) != 1 or ord(key) < 32:
                continue
            buf.append(key)
            sys.stdout.write(mask)
            sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.write("\n")
        sys.stdout.flush()
    return "".join(buf)
