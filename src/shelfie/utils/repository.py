from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

class LibraryRepositoryJson:
    """Persist the library catalogue to a JSON file.

    The repository keeps a lightweight ``library.json`` alongside an automatic
    ``library.bak.json`` backup so manual edits or crashes can be recovered
    easily.  Call :meth:`save` after every library mutation.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.backup_path = path.with_suffix(".bak.json")

    def load(self) -> List[dict]:
        if not self.path.exists():
            return []
        try:
            raw = self.path.read_text(encoding="utf-8")
        except OSError:
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []
        books = data.get("books")
        if not isinstance(books, list):
            return []
        return [item for item in books if isinstance(item, dict)]

    def save(self, books: Iterable[dict | object]) -> None:
        payload = {"books": []}
        for book in books:
            if hasattr(book, "as_dict"):
                method = getattr(book, "as_dict")
                if callable(method):
                    payload["books"].append(method())
                    continue
            if isinstance(book, dict):
                payload["books"].append(dict(book))
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                self.backup_path.write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")
            except OSError:
                pass
        self.path.write_text(text, encoding="utf-8")


__all__ = ["LibraryRepositoryJson"]
