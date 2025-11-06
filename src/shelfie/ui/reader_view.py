from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

try:  # pragma: no cover - optional dependency
    import fitz  # type: ignore
except Exception:  # noqa: BLE001
    import importlib

    fitz = importlib.import_module("fitz")  # type: ignore

FITZ_AVAILABLE = not getattr(fitz, "__STUB__", False)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QShortcut,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from shelfie.database import reading
from shelfie.importers.pipeline import ImportPipeline
from shelfie.models.library_model import BookRecord
from shelfie.tts.service import TTSService
from shelfie.ui.tts_bar import TTSBar

LOGGER = logging.getLogger(__name__)


class ReaderView(QWidget):
    reading_state_updated = Signal()

    def __init__(
        self,
        conn: sqlite3.Connection,
        pipeline: ImportPipeline,
        tts_service: TTSService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._conn = conn
        self.pipeline = pipeline
        self._tts = tts_service
        self._doc: fitz.Document | None = None
        self._book: BookRecord | None = None
        self._page_index = 0
        self._page_count = 0

        self._title_label = QLabel("No book open", self)
        self._page_indicator = QLabel("Page 0 / 0", self)

        self._page_label = QLabel("Drop a book from the library to begin", self)
        self._page_label.setAlignment(Qt.AlignCenter)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(self._page_label)

        self._page_slider = QSlider(Qt.Horizontal, self)
        self._page_slider.setRange(1, 1)
        self._page_slider.setEnabled(False)
        self._page_slider.valueChanged.connect(self._on_page_slider_changed)

        self._zoom_slider = QSlider(Qt.Horizontal, self)
        self._zoom_slider.setMinimum(25)
        self._zoom_slider.setMaximum(250)
        self._zoom_slider.setValue(100)
        self._zoom_slider.valueChanged.connect(self._render_page)

        self._open_button = QPushButton("Import & Open…", self)
        self._open_button.clicked.connect(self._open_pdf_dialog)

        self._prev_button = QToolButton(self)
        self._prev_button.setText("◀")
        self._prev_button.clicked.connect(self.previous_page)

        self._next_button = QToolButton(self)
        self._next_button.setText("▶")
        self._next_button.clicked.connect(self.next_page)

        controls = QHBoxLayout()
        controls.addWidget(self._open_button)
        controls.addSpacing(12)
        controls.addWidget(self._prev_button)
        controls.addWidget(self._next_button)
        controls.addSpacing(12)
        controls.addWidget(self._title_label, 1)
        controls.addWidget(self._page_indicator)

        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("Page", self))
        slider_row.addWidget(self._page_slider, 1)
        slider_row.addSpacing(12)
        slider_row.addWidget(QLabel("Zoom", self))
        slider_row.addWidget(self._zoom_slider)

        self._tts_bar = TTSBar(self)
        self._tts_bar.play_requested.connect(self._on_play_requested)
        self._tts_bar.stop_requested.connect(self._on_stop_requested)
        self._tts_bar.voice_changed.connect(self._on_voice_changed)
        self._tts_bar.speed_changed.connect(self._on_speed_changed)
        self._tts_bar.pitch_changed.connect(self._on_pitch_changed)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addLayout(slider_row)
        layout.addWidget(self._scroll, 1)
        layout.addWidget(self._tts_bar)
        self.setLayout(layout)

        open_shortcut = QShortcut(QKeySequence.Open, self)
        open_shortcut.activated.connect(self._open_pdf_dialog)

        next_shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        next_shortcut.activated.connect(self.next_page)
        prev_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        prev_shortcut.activated.connect(self.previous_page)

        self._tts.started.connect(lambda: self._tts_bar.set_playing(True))
        self._tts.finished.connect(self._on_tts_finished)
        self._tts.error.connect(self._on_tts_error)

    # -- file handling --------------------------------------------------
    def open_book(self, record: BookRecord) -> None:
        self._close_document()
        self._book = record
        self._title_label.setText(record.title)
        if not FITZ_AVAILABLE:
            self._page_label.setText("PyMuPDF is unavailable; install pymupdf to enable reading.")
            return
        try:
            self._doc = fitz.open(record.file_path)
        except Exception:  # noqa: BLE001
            LOGGER.exception("Failed to open PDF: %s", record.file_path)
            QMessageBox.warning(self, "Reader", f"Unable to open {record.file_path}")
            return

        self._page_count = getattr(self._doc, "page_count", 0) or 1
        state = reading.load_state(self._conn, record.id)
        self._page_index = min(max(state.last_page, 0), self._page_count - 1)
        self._page_slider.setRange(1, self._page_count)
        self._page_slider.setEnabled(True)
        self._update_page_controls()
        self._render_page()

        self._tts.stop()
        self._tts.load_book(record.id)
        prefs = self._tts.current_preferences()
        self._tts_bar.set_voice_options(self._tts.available_voices(), prefs.voice_id)
        self._tts_bar.set_speed_value(prefs.speed)
        self._tts_bar.set_pitch_value(prefs.pitch)
        self._tts_bar.set_status("Ready")

    def _open_pdf_dialog(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(self, "Import PDF", str(Path.home()), "PDF Files (*.pdf)")
        if not file_name:
            return
        results = self.pipeline.ingest([Path(file_name)])
        if not results:
            return
        record = self._record_for_book(results[0].book_id)
        if record:
            self.open_book(record)

    def _close_document(self) -> None:
        self._tts.stop()
        if self._doc is not None:
            try:
                self._doc.close()
            except Exception:  # noqa: BLE001
                LOGGER.debug("Error closing PDF", exc_info=True)
            self._doc = None
        self._page_count = 0

    # -- rendering -------------------------------------------------------
    def _render_page(self) -> None:
        if self._doc is None or not FITZ_AVAILABLE:
            return
        try:
            page = self._doc.load_page(self._page_index)
            zoom = self._zoom_slider.value() / 100.0
            mat = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=mat, alpha=False)
            image = QImage(
                pixmap.samples,
                pixmap.width,
                pixmap.height,
                pixmap.stride,
                QImage.Format_RGB888,
            )
            pix = QPixmap.fromImage(image)
            self._page_label.setPixmap(pix)
            self._page_label.resize(pix.size())
            self._update_page_controls()
            self._update_reading_state()
        except Exception:  # noqa: BLE001
            LOGGER.exception("Failed to render page")

    def _update_page_controls(self) -> None:
        self._page_indicator.setText(f"Page {self._page_index + 1} / {max(self._page_count, 1)}")
        if self._page_slider.maximum() != max(self._page_count, 1):
            self._page_slider.setRange(1, max(self._page_count, 1))
        self._page_slider.blockSignals(True)
        self._page_slider.setValue(self._page_index + 1)
        self._page_slider.blockSignals(False)

    def _update_reading_state(self) -> None:
        if self._book is None or self._doc is None:
            return
        percent = (self._page_index + 1) / max(self._page_count, 1)
        reading.save_state(
            self._conn,
            reading.ReadingState(
                book_id=self._book.id,
                last_page=self._page_index,
                percent=percent,
            ),
        )
        self.reading_state_updated.emit()

    # -- navigation -------------------------------------------------------
    def next_page(self) -> None:
        if self._doc and self._page_index < self._page_count - 1:
            self._page_index += 1
            self._render_page()

    def previous_page(self) -> None:
        if self._doc and self._page_index > 0:
            self._page_index -= 1
            self._render_page()

    def _on_page_slider_changed(self, value: int) -> None:
        if self._doc is None:
            return
        self._page_index = max(0, min(value - 1, self._page_count - 1))
        self._render_page()

    # -- text-to-speech ---------------------------------------------------
    def _on_play_requested(self) -> None:
        if not FITZ_AVAILABLE or self._doc is None:
            self._tts_bar.set_status("Install pymupdf to enable text-to-speech")
            return
        text = self._current_page_text()
        if not text.strip():
            self._tts_bar.set_status("No readable text on this page")
            return
        self._tts_bar.set_playing(True)
        self._tts.speak(text)

    def _on_stop_requested(self) -> None:
        self._tts.stop()
        self._tts_bar.set_playing(False)

    def _on_voice_changed(self, voice_id: str) -> None:
        self._tts.set_voice(voice_id or None)

    def _on_speed_changed(self, speed: float) -> None:
        self._tts.set_speed(speed)

    def _on_pitch_changed(self, pitch: float) -> None:
        self._tts.set_pitch(pitch)

    def _on_tts_finished(self) -> None:
        self._tts_bar.set_playing(False)

    def _on_tts_error(self, message: str) -> None:
        self._tts_bar.set_playing(False)
        self._tts_bar.set_status(message)

    def _current_page_text(self) -> str:
        if self._doc is None:
            return ""
        try:
            page = self._doc.load_page(self._page_index)
            return page.get_text("text")
        except Exception:  # noqa: BLE001
            LOGGER.debug("Failed to extract text", exc_info=True)
            return ""

    # -- helpers ----------------------------------------------------------
    def _record_for_book(self, book_id: int) -> BookRecord | None:
        row = self._conn.execute(
            """
            SELECT b.id, b.title, b.author, b.year, b.file_path, a.cover_path, rs.percent
            FROM books b
            LEFT JOIN book_assets a ON a.book_id = b.id
            LEFT JOIN reading_state rs ON rs.book_id = b.id
            WHERE b.id = ?
            """,
            (book_id,),
        ).fetchone()
        if row is None:
            return None
        return BookRecord(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            year=row["year"],
            cover_path=Path(row["cover_path"]) if row["cover_path"] else None,
            progress=(row["percent"] or 0) / 100.0,
            file_path=Path(row["file_path"]),
        )

    def closeEvent(self, event) -> None:  # noqa: N802
        self._close_document()
        super().closeEvent(event)
