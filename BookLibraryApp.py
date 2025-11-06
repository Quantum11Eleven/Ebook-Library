"""Shelfie Book Library App launcher.

Double-click or run this single file to start the Shelfie GUI.  It ensures the
project source directory is available on ``sys.path`` and then delegates to the
existing application entry point, keeping command-line flags like
``--headless`` intact.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, List, Optional


def _ensure_src_on_path() -> None:
    """Prepend the repository ``src`` directory to ``sys.path`` if needed."""

    repo_root = Path(__file__).resolve().parent
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Launch Shelfie via :mod:`shelfie.main`.

    Parameters
    ----------
    argv:
        Optional iterable of CLI arguments to forward.  When *None*, the
        current ``sys.argv[1:]`` is used so flags like ``--headless`` keep
        working when the file is executed directly.
    """

    _ensure_src_on_path()

    from shelfie.main import main as shelfie_main  # imported lazily

    if argv is None:
        forwarded: Optional[List[str]] = None
    else:
        forwarded = list(argv)

    return shelfie_main(forwarded)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
