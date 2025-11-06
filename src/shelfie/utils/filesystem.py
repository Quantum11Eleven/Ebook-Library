from __future__ import annotations

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable


def sha256sum(path: Path, chunk_size: int = 1_048_576) -> str:
    """Compute a streaming SHA-256 hash for the given file."""
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_or_link(source: Path, destination: Path, mode: str = "copy") -> Path:
    """Copy or link a file into the destination path."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if mode == "copy":
        shutil.copy2(source, destination)
    elif mode == "link":
        if os.name == "nt":
            shutil.copy2(source, destination)
        else:
            if destination.exists():
                destination.unlink()
            os.link(source, destination)
    else:
        msg = "mode must be 'copy' or 'link'"
        raise ValueError(msg)
    return destination


def timestamp() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def ensure_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
