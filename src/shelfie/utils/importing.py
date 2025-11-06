"""Utilities for expanding and normalising PDF import paths."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


def _normalise(path: Path) -> str:
    """Return a normalised string representation of *path*.

    Paths are resolved where possible so that duplicate selections that refer
    to the same file (e.g. relative and absolute references) collapse to a
    single entry.  The function falls back to ``absolute()`` so missing files
    simply get skipped by the caller.
    """

    try:
        return str(path.resolve(strict=False))
    except OSError:
        return str(path.absolute())


def collect_pdf_paths(paths: Iterable[str]) -> List[str]:
    """Expand *paths* into a unique list of PDF files.

    The helper accepts files and directories.  Directories are scanned
    recursively for ``.pdf`` files and the resulting list preserves the
    user-supplied order: files are yielded as provided, followed by matches
    discovered within each directory.
    """

    seen: set[str] = set()
    resolved: List[str] = []

    for raw in paths:
        if not raw:
            continue

        candidate = Path(raw).expanduser()
        if candidate.is_dir():
            for nested in sorted(candidate.rglob("*.pdf")):
                if not nested.is_file():
                    continue
                normalised = _normalise(nested)
                if normalised in seen:
                    continue
                seen.add(normalised)
                resolved.append(normalised)
            continue

        if not candidate.is_file() or candidate.suffix.lower() != ".pdf":
            continue

        normalised = _normalise(candidate)
        if normalised in seen:
            continue
        seen.add(normalised)
        resolved.append(normalised)

    return resolved


__all__ = ["collect_pdf_paths"]
