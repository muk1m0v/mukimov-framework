"""Create a runnable mukimov.web project in a new directory."""

from contextlib import ExitStack, suppress
from pathlib import Path
from textwrap import dedent
import argparse
import re
import sys

from .cli import _ensure_utf8


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
        from mukimov.dirs import BASE_DIR

        DEBUG = True
        HTML_TEMPLATES = [BASE_DIR / "templates"]
        ALL_CONTENT_STATIC = True

        CSS_SETTING = {"STYLE_MAIN_PATH": "/content/css/"}
        JAVASCRIPT_SETTING = {"SCRIPT_MAIN_PATH": "/content/js/"}
        IMAGE_SETTING = {"IMAGE_MAIN_PATH": "/content/img/"}
    """,
    "templates/index.html": "",
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
