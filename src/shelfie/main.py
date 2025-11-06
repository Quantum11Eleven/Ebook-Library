"""Shelfie entrypoint with environment guard and optional headless mode."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import bootstrap
from .cli_stub import main as cli_main


def run_gui() -> int:
    from PySide6.QtWidgets import QApplication  # type: ignore

    from .ui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="shelfie")
    parser.add_argument("--headless", action="store_true", help="Run without GUI")
    args = parser.parse_args(argv)

    if args.headless:
        return cli_main([])

    if not bootstrap.has_pyside6():
        bootstrap.print_missing_and_exit(1)

    return run_gui()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
