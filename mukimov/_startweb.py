"""Create a runnable mukimov.web project."""

from contextlib import ExitStack, suppress
from pathlib import Path
from textwrap import dedent
import argparse
import re
import sys

from .color import _ensure_utf8


_DIRECTORIES = ("core", "templates", "content", "content/css", "content/js", "content/img")
_FILES = {
    "app.py": """
        from mukimov.web import App, render_template

        app = App()


        @app.route("/")
        def home():
            return render_template("index.html")


        if __name__ == "__main__":
            app.run()
    """,
    "core/conf.py": """
        # Корень проекта: папка с app.py, независимо от папки запуска терминала.
        # Пример пути к файлу: BASE_DIR / "content" / "css" / "style.css"
        from mukimov.dirs import BASE_DIR

        # В Python логические значения пишутся True и False.
        # True: встроенная главная для пустого index.html и подсказки на страницах ошибок.
        # Пример отключения: DEBUG = False
        DEBUG = True

        # Показывать цветные строки HTTP-запросов в терминале.
        # Пример: SHOW_SERVER_STATUS_IN_TERMINAL = False скрывает строки GET/POST и статусы.
        # Сообщения запуска и ошибки приложения остаются видны.
        SHOW_SERVER_STATUS_IN_TERMINAL = True

        # Каталоги HTML-шаблонов проверяются по порядку.
        # Пример: HTML_TEMPLATES = [BASE_DIR / "pages", BASE_DIR / "templates"]
        # В app.py: return render_template("index.html", title="Мой сайт")
        HTML_TEMPLATES = [BASE_DIR / "templates"]

        # True: разрешены короткие имена ресурсов в HTML, объявленные ниже.
        # False: используй прямые адреса, например href="/content/css/style.css".
        # Пример короткого имени: href="{$ 'main_style' $}"
        ALL_CONTENT_STATIC = True

        # CSS-файлы. Путь задаёт адрес в браузере и папку внутри корня проекта.
        # Пример другого пути: "STYLE_MAIN_PATH": "/assets/css/"
        CSS_SETTING = {
            "STYLE_MAIN_PATH": "/content/css/",
            # Создай content/css/style.css, затем раскомментируй следующую строку.
            # "style.css": "main_style",
        }
        # HTML: <link rel="stylesheet" href="{$ 'main_style' $}">

        # JavaScript-файлы. В этой папке разрешены файлы .js и .mjs.
        # Пример другого пути: "SCRIPT_MAIN_PATH": "/assets/js/"
        JAVASCRIPT_SETTING = {
            "SCRIPT_MAIN_PATH": "/content/js/",
            # Создай content/js/script.js, затем раскомментируй следующую строку.
            # "script.js": "my_script",
        }
        # HTML: <script src="{$ 'my_script' $}" defer></script>

        # Изображения. Например, PNG, JPEG, SVG или WebP.
        # Пример другого пути: "IMAGE_MAIN_PATH": "/assets/img/"
        IMAGE_SETTING = {
            "IMAGE_MAIN_PATH": "/content/img/",
            # Создай content/img/logo.png, затем раскомментируй следующую строку.
            # "logo.png": "logo",
        }
        # HTML: <img src="{$ 'logo' $}" alt="Логотип">
    """,
    "templates/index.html": "",
}


def _cleanup(remove):
    with suppress(OSError):
        remove()


def main(argv=None) -> int:
    _ensure_utf8()
    parser = argparse.ArgumentParser(prog="mukimov-startweb", description="Create a new web project.")
    parser.add_argument("name", nargs="?", help="Optional new directory (default: current directory)")
    name = parser.parse_args(argv).name
    if name is not None and not re.fullmatch(r"[\w-]+", name):
        parser.error("Use letters, numbers, underscores or hyphens for the project name.")
    reserved = {"core", "content", "templates"}
    root = Path.cwd().resolve()
    if root.name.casefold() in reserved:
        parser.error("Run startweb from the project root, one level above this directory.")
    if name is not None and name.casefold() in reserved:
        parser.error("Choose a project name other than core, content, or templates.")

    project = root if name is None else root / name
    try:
        with ExitStack() as cleanup:
            if name is not None:
                project.mkdir()
                cleanup.callback(_cleanup, project.rmdir)
            for directory in _DIRECTORIES:
                path = project / directory
                try:
                    path.mkdir()
                except FileExistsError:
                    if not path.is_dir() or path.is_symlink() or path.resolve() != path:
                        raise
                else:
                    cleanup.callback(_cleanup, path.rmdir)
            for filename, source in _FILES.items():
                path = project / filename
                if filename == "templates/index.html" and path.is_file():
                    continue
                with path.open("x", encoding="utf-8") as file:
                    cleanup.callback(_cleanup, path.unlink)
                    file.write(dedent(source).lstrip("\n"))
            cleanup.pop_all()
    except FileExistsError as error:
        print(f"Не удалось создать проект: уже существует {error.filename}.", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"Не удалось создать проект в {project}: {error}", file=sys.stderr)
        return 1

    print(f"Проект создан: {project}")
    print("Запуск: python app.py" if name is None else f"Запуск: cd {name}, затем python app.py")
    return 0
