"""Create a runnable mukimov.web project in a new directory."""

from contextlib import ExitStack, suppress
from pathlib import Path
from textwrap import dedent
import argparse
import re
import sys

from .cli import _ensure_utf8


_DIRECTORIES = ("templates", "content", "content/css", "content/js", "content/img")
_FILES = {
    "app.py": """
        from pathlib import Path

        from mukimov.web import App, render_template

        app = App()


        @app.route("/")
        def home():
            return render_template("index.html", title=Path(__file__).resolve().parent.name)


        if __name__ == "__main__":
            app.run()
    """,
    "conf.py": """
        ALL_CONTENT_STATIC = True

        CSS_SETTING = {
            "STYLE_MAIN_PATH": "/content/css/",
            "style.css": "main_style",
        }

        JAVASCRIPT_SETTING = {
            "SCRIPT_MAIN_PATH": "/content/js/",
            "script.js": "my_script",
        }

        IMAGE_SETTING = {
            "IMAGE_MAIN_PATH": "/content/img/",
            "example.svg": "example_photo",
        }
    """,
    "templates/index.html": """
        <!doctype html>
        <html lang="ru">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>{{ title }}</title>
            <link rel="stylesheet" href="{$ 'main_style' $}">
            <script src="{$ 'my_script' $}" defer></script>
        </head>
        <body>
            <main>
                <img src="{$ 'example_photo' $}" width="48" height="48" alt="">
                <h1>{{ title }}</h1>
                <p>Сайт работает. Пути к CSS, JavaScript и изображению заданы в conf.py.</p>
                <button type="button" id="hello">Проверить JavaScript</button>
                <p id="status" role="status"></p>
            </main>
        </body>
        </html>
    """,
    "content/css/style.css": """
        body { margin: 0; color: #111; background: #fff; font: 1rem/1.6 system-ui, sans-serif; }
        main { max-width: 40rem; margin: 4rem auto; padding: 0 1rem; }
        button { font: inherit; color: #fff; background: #111; border: 0; padding: .5rem 1rem; cursor: pointer; }
    """,
    "content/js/script.js": """
        document.querySelector("#hello").addEventListener("click", () => {
            document.querySelector("#status").textContent = "JavaScript работает!";
        });
    """,
    "content/img/example.svg": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
            <rect width="48" height="48" rx="8" fill="#111"/>
            <path d="m13 16 8 8-8 8m12 0h10" fill="none" stroke="#fff" stroke-width="3"/>
        </svg>
    """,
}


def _cleanup(remove):
    with suppress(OSError):
        remove()


def main(argv=None) -> int:
    _ensure_utf8()
    parser = argparse.ArgumentParser(prog="mukimov-startweb", description="Create a new web project.")
    parser.add_argument("name", help="Name of the directory to create here")
    name = parser.parse_args(argv).name
    if not re.fullmatch(r"[\w-]+", name):
        parser.error("Use letters, numbers, underscores or hyphens for the project name.")

    project = Path.cwd() / name
    try:
        with ExitStack() as cleanup:
            project.mkdir()
            cleanup.callback(_cleanup, project.rmdir)
            for directory in _DIRECTORIES:
                path = project / directory
                path.mkdir()
                cleanup.callback(_cleanup, path.rmdir)
            for filename, source in _FILES.items():
                path = project / filename
                with path.open("x", encoding="utf-8") as file:
                    cleanup.callback(_cleanup, path.unlink)
                    file.write(dedent(source).lstrip("\n"))
            cleanup.pop_all()
    except FileExistsError:
        print(f"Не удалось создать проект: {name} уже существует.", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"Не удалось создать проект {name}: {error}", file=sys.stderr)
        return 1

    print(f"Проект создан: {project}")
    print(f"Запуск: cd {name}, затем python app.py")
    return 0
