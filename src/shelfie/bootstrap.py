"""Environment bootstrap and helpful guidance.

This module isolates checks so importing it never requires PySide6.
Tests target these functions to avoid GUI deps in CI/sandboxes.
"""
from __future__ import annotations

import importlib.util
import platform
import sys
from textwrap import dedent


def has_pyside6() -> bool:
    """Return True if PySide6 is importable in this interpreter."""
    return importlib.util.find_spec("PySide6") is not None


essentials_hint = (
    "\n  # If full PySide6 fails on Linux servers, try just the essentials:\n"
    "  pip install PySide6-Essentials\n"
)


def missing_pyside6_message() -> str:
    os_name = platform.system()
    if os_name == "Windows":
        install = "pip install PySide6"
        shell = "PowerShell"
        activate = ". .venv/Scripts/Activate.ps1"
    else:
        install = "python3 -m pip install PySide6"
        shell = "bash/zsh"
        activate = "source .venv/bin/activate"

    return dedent(
        f"""
        ⛔ PySide6 is not installed in this environment.

        To run the Shelfie GUI, create/activate a virtual env and install deps:

          {shell}:
            python -m venv .venv
            {activate}
            pip install --upgrade pip
            pip install -r requirements.txt
            # or explicitly:
            {install}
            {essentials_hint if os_name != 'Windows' else ''}  
        Then launch:
            python -m src.shelfie.main

        If you cannot install GUI deps (e.g., sandbox/CI), use headless mode:
            python -m src.shelfie.main --headless
        """
    )


def print_missing_and_exit(code: int = 1) -> None:
    sys.stderr.write(missing_pyside6_message())
    sys.stderr.flush()
    raise SystemExit(code)
