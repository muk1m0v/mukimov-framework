"""Interactive tour of the public mukimov features."""

import os
import sys
from pathlib import Path

from mukimov import __version__, cli, color, env, stars
from mukimov.password import hash_password, high, low, medium, verify_password
from mukimov.text import markdown


def read_choice(prompt: str) -> str:
    """Read one menu key in a terminal, or one line when input is redirected."""
    if not sys.stdin.isatty():
        return input(prompt).strip()

    print(prompt, end="", flush=True)
    if os.name == "nt":
        import msvcrt

        key = msvcrt.getwch()
        if key in ("\x00", "\xe0"):
            msvcrt.getwch()
            key = ""
    else:
        import termios
        import tty

        fd = sys.stdin.fileno()
        original = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            data = os.read(fd, 1)
            if not data:
                raise EOFError
            if data == b"\x1b":
                termios.tcflush(fd, termios.TCIFLUSH)
            key = data.decode("ascii", errors="ignore")
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, original)

    print(key if key in "0123456" else "")
    if key in ("\x04", "\x1a"):
        raise EOFError
    if key == "\x03":
        raise KeyboardInterrupt
    return key


def show_mask() -> None:
    print("Введи тестовый пароль. Попробуй Backspace, затем нажми Enter.")
    try:
        stars(color.cyan("Пароль: "), mask="*")
    except RuntimeError:
        print(color.red("Для скрытого ввода запусти пример в обычном терминале."))
        return
    print(color.green("Пароль принят."))


def show_hash() -> None:
    print("1 · low    2 · medium    3 · high    0 · Назад")
    choice = read_choice("Уровень: ")
    if choice == "0":
        return
    level = {"1": low, "2": medium, "3": high}.get(choice)
    if level is None:
        print(color.yellow("Выбери уровень от 1 до 3."))
        return

    password = "1234ok"
    stored = hash_password(password, level=level)
    print(f"Тестовый пароль: {password}")
    print(f"Хеш {level} ({len(stored)} символов):\n{stored}")
    print(f"Проверка верного пароля: {verify_password(password, stored)}")
    print(f"Проверка неверного пароля: {verify_password('wrong', stored)}")


def show_colors() -> None:
    for name in color.__all__:
        paint = getattr(color, name)
        print(f"  {paint(name)}")


def show_markdown() -> None:
    markdown.print("""# Отчёт

- **API** отвечает
- *База данных* на связи

| Сервис | Статус |
| --- | --- |
| API | 200 OK |
| База данных | Подключена |
""")
    rendered = markdown.render("Результат проверки — **готово**.")
    print(rendered)


def show_settings() -> None:
    path = Path(__file__).with_name("example.env")
    env.load(path, override=True)
    env.check(["MUKIMOV_EXAMPLE_TITLE", "MUKIMOV_EXAMPLE_URL"])
    title = env.string("MUKIMOV_EXAMPLE_TITLE")
    url = env.required("MUKIMOV_EXAMPLE_URL")
    debug = env.boolean("MUKIMOV_EXAMPLE_DEBUG", default=False)
    port = env.integer("MUKIMOV_EXAMPLE_PORT", default=8080, min=1, max=65535)
    hosts = env.list("MUKIMOV_EXAMPLE_HOSTS", separator=",")
    print(f"{title}\nURL: {url}\nDEBUG: {debug}\nПорт: {port}\nХосты: {', '.join(hosts)}")


def show_cli() -> None:
    cli.main(["--version"])
    cli.main(["--help"])
    cli.main(["doctor"])


MENU = {
    "1": ("Проверить маску пароля", show_mask),
    "2": ("Хешировать и проверить пароль", show_hash),
    "3": ("Посмотреть цвета", show_colors),
    "4": ("Вывести Markdown", show_markdown),
    "5": ("Загрузить настройки из .env", show_settings),
    "6": ("Открыть справку и диагностику CLI", show_cli),
}


def main() -> None:
    while True:
        print(color.cyan(f"\nmukimov {__version__} · примеры"))
        for key, (label, _) in MENU.items():
            print(f"  {key} · {label}")
        print("  0 · Выход")

        try:
            choice = read_choice("Выбери пункт: ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == "0":
            return
        if choice not in MENU:
            print(color.yellow("Выбери пункт от 0 до 6."))
            continue

        try:
            MENU[choice][1]()
        except (EOFError, KeyboardInterrupt):
            print("\nВозврат в меню.")
        except (env.EnvError, OSError) as exc:
            print(color.red(f"Ошибка: {exc}"))
