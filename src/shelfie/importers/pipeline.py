from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Protocol

try:  # pragma: no cover - optional dependency
    import fitz  # type: ignore
except Exception:  # noqa: BLE001
    import importlib

    fitz = importlib.import_module("fitz")  # type: ignore

FITZ_AVAILABLE = not getattr(fitz, "__STUB__", False)

try:  # pragma: no cover - optional dependency
    from PIL import Image
except Exception:  # noqa: BLE001
    Image = None  # type: ignore[assignment]

from shelfie.utils.filesystem import copy_or_link, ensure_directories, sha256sum, timestamp
from shelfie.utils.qt import ProgressSignal

LOGGER = logging.getLogger(__name__)


@dataclass
class ImportOptions:
    library_root: Path
    copy_mode: str = "copy"
    cover_size: tuple[int, int] = (512, 512)


@dataclass
class ImportResult:
    book_id: int
    file_path: Path
    metadata: dict[str, object]


class PipelineObserver(Protocol):
    def on_duplicate(self, path: Path) -> None:
        ...

    def on_imported(self, result: ImportResult) -> None:
        ...


class ImportPipeline:
    """Coordinate file ingestion and metadata persistence."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        options: ImportOptions,
        observer: PipelineObserver | None = None,
    ) -> None:
        self.conn = conn
        self.options = options
        self.observer = observer
        self.signals = ProgressSignal()
        ensure_directories([self.options.library_root])

    # -- public API -----------------------------------------------------------------
    def ingest(self, paths: Iterable[Path]) -> list[ImportResult]:
        results: list[ImportResult] = []
        for index, path in enumerate(self._iter_files(paths), start=1):
            try:
                result = self._ingest_single(path)
            except DuplicateFileError:
                LOGGER.info("Duplicate skipped: %s", path)
                if self.observer:
                    self.observer.on_duplicate(path)
                continue
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("Failed to ingest %s", path)
                self.signals.failed.emit(str(exc))
                continue

            results.append(result)
            if self.observer:
                self.observer.on_imported(result)
            self.signals.progressed.emit(index, path.name)

        self.signals.completed.emit()
        return results

    # -- internal helpers -----------------------------------------------------------
    def _iter_files(self, paths: Iterable[Path]) -> Iterator[Path]:
        for path in paths:
            if path.is_dir():
                yield from (child for child in path.rglob("*.pdf"))
            elif path.suffix.lower() == ".pdf":
                yield path

    def _ingest_single(self, source_path: Path) -> ImportResult:
        file_hash = sha256sum(source_path)
        if self._is_duplicate(file_hash):
            raise DuplicateFileError(source_path)

        destination = self._destination_for(source_path)
        stored_file = copy_or_link(source_path, destination, mode=self.options.copy_mode)

        metadata = self._extract_metadata(stored_file)
        cover_path, thumb_path = self._render_covers(stored_file)

        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO books (title, author, year, isbn, file_path, file_hash, pages, added_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metadata["title"],
                    metadata.get("author"),
                    metadata.get("year"),
                    metadata.get("isbn"),
                    str(stored_file),
                    file_hash,
                    metadata.get("pages", 0),
                    timestamp(),
                    timestamp(),
                ),
            )
            book_id = cursor.lastrowid

            self.conn.execute(
                """
                INSERT OR REPLACE INTO book_assets (book_id, cover_path, thumb_path)
                VALUES (?, ?, ?)
                """,
                (book_id, str(cover_path) if cover_path else None, str(thumb_path) if thumb_path else None),
            )

        metadata_payload = {
            "title": metadata["title"],
            "author": metadata.get("author"),
            "pages": metadata.get("pages", 0),
            "year": metadata.get("year"),
            "isbn": metadata.get("isbn"),
            "cover_path": str(cover_path) if cover_path else None,
            "thumb_path": str(thumb_path) if thumb_path else None,
        }

        return ImportResult(book_id=book_id, file_path=stored_file, metadata=metadata_payload)

    def _is_duplicate(self, file_hash: str) -> bool:
        query = "SELECT 1 FROM books WHERE file_hash = ? LIMIT 1"
        cursor = self.conn.execute(query, (file_hash,))
        return cursor.fetchone() is not None

    def _destination_for(self, source_path: Path) -> Path:
        metadata = self._extract_metadata(source_path)
        year = metadata.get("year") or "unknown"
        title_slug = metadata.get("title") or source_path.stem
        safe_title = _slugify(str(title_slug))
        year_folder = str(year)
        destination_folder = self.options.library_root / year_folder / safe_title
        ensure_directories([destination_folder])
        return destination_folder / source_path.name

    def _extract_metadata(self, pdf_path: Path) -> dict[str, object]:
        if not FITZ_AVAILABLE:
            return _fallback_metadata(pdf_path)

        try:
            doc = fitz.open(pdf_path)
        except Exception:  # noqa: BLE001
            LOGGER.debug("PyMuPDF failed to open %s; using fallback metadata", pdf_path, exc_info=True)
            return _fallback_metadata(pdf_path)

        info = doc.metadata or {}
        title = info.get("title") or pdf_path.stem
        author = info.get("author") or None
        year = _parse_year(info.get("creationDate") or info.get("modDate"))
        pages = getattr(doc, "page_count", 0)
        doc.close()

        try:
            isbn = _guess_isbn(pdf_path.stem)
        except ValueError:
            isbn = None

        return {
            "title": title,
            "author": author,
            "year": year,
            "isbn": isbn,
            "pages": pages,
        }

    def _render_covers(self, pdf_path: Path) -> tuple[Path | None, Path | None]:
        if not FITZ_AVAILABLE or Image is None:
            return None, None

        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(0)
            pix = page.get_pixmap(alpha=False)
        except Exception:  # noqa: BLE001
            LOGGER.exception("Cover rendering failed for %s", pdf_path)
            return None, None
        finally:
            try:
                doc.close()
            except Exception:  # noqa: BLE001
                pass

        cover_dir = self.options.library_root / "_covers"
        thumb_dir = cover_dir / "thumbnails"
        ensure_directories([cover_dir, thumb_dir])

        cover_path = cover_dir / f"{pdf_path.stem}.png"
        thumb_path = thumb_dir / f"{pdf_path.stem}_thumb.png"

        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        image.save(cover_path, format="PNG")

        thumb = image.copy()
        thumb.thumbnail(self.options.cover_size)
        thumb.save(thumb_path, format="PNG")

        return cover_path, thumb_path


class DuplicateFileError(RuntimeError):
    def __init__(self, path: Path) -> None:
        super().__init__(f"Duplicate file skipped: {path}")
        self.path = path


def _slugify(value: str) -> str:
    sanitized = "".join(ch if ch.isalnum() or ch in (" ", "-", "_") else " " for ch in value)
    collapsed = "-".join(filter(None, sanitized.lower().split()))
    return collapsed or "book"


def _parse_year(date_str: str | None) -> int | None:
    if not date_str:
        return None
    digits = "".join(ch for ch in date_str if ch.isdigit())
    if len(digits) >= 4:
        return int(digits[:4])
    return None


def _guess_isbn(name: str) -> str | None:
    digits = "".join(ch for ch in name if ch.isdigit())
    if len(digits) in {10, 13}:
        return digits
    raise ValueError("No ISBN found")


def _fallback_metadata(pdf_path: Path) -> dict[str, object]:
    try:
        isbn = _guess_isbn(pdf_path.stem)
    except ValueError:
        isbn = None

    return {
        "title": pdf_path.stem,
        "author": None,
        "year": None,
        "isbn": isbn,
        "pages": 0,
    }
