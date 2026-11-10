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
