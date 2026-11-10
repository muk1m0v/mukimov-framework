"""Run the CLI with ``python -m mukimov`` even without Scripts in PATH."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
