from __future__ import annotations

import logging
from pathlib import Path

try:  # pragma: no cover - optional dependency
    import fitz  # type: ignore
except Exception:  # noqa: BLE001
    import importlib

    fitz = importlib.import_module("fitz")  # type: ignore

FITZ_AVAILABLE = not getattr(fitz, "__STUB__", False)
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QScrollArea,
    QShortcut,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from shelfie.importers.pipeline import ImportPipeline

LOGGER = logging.getLogger(__name__)


class ReaderView(QWidget):
    def __init__(self, pipeline: ImportPipeline, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.pipeline = pipeline
        self._doc: fitz.Document | None = None
        self._page_index = 0

        self._page_label = QLabel("Drop a book from the library to begin", self)
        self._page_label.setAlignment(Qt.AlignCenter)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(self._page_label)

        self._zoom_slider = QSlider(Qt.Horizontal, self)
        self._zoom_slider.setMinimum(10)
        self._zoom_slider.setMaximum(300)
        self._zoom_slider.setValue(100)
        self._zoom_slider.valueChanged.connect(self._render_page)

        layout = QVBoxLayout(self)
        layout.addWidget(self._scroll)
        layout.addWidget(self._zoom_slider)
        self.setLayout(layout)

        open_shortcut = QShortcut(QKeySequence.Open, self)
        open_shortcut.activated.connect(self._open_pdf_dialog)

    # -- file handling --------------------------------------------------------------
    def open_document(self, path: Path) -> None:
        self._close_document()
        if not FITZ_AVAILABLE:
            LOGGER.warning("PyMuPDF is unavailable; reader cannot open %s", path)
            return
        try:
            self._doc = fitz.open(path)
        except Exception:  # noqa: BLE001
            LOGGER.exception("Failed to open PDF: %s", path)
            return
        self._page_index = 0
        self._render_page()

    def _open_pdf_dialog(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF", str(Path.home()), "PDF Files (*.pdf)")
        if file_name:
            self.open_document(Path(file_name))

    def _close_document(self) -> None:
        if self._doc is not None:
            try:
                self._doc.close()
            except Exception:  # noqa: BLE001
                LOGGER.debug("Error closing PDF", exc_info=True)
            self._doc = None

    # -- rendering ------------------------------------------------------------------
    def _render_page(self) -> None:
        if self._doc is None or not FITZ_AVAILABLE:
            return
        try:
            page = self._doc.load_page(self._page_index)
            zoom = self._zoom_slider.value() / 100.0
            mat = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=mat, alpha=False)
            image = QImage(pixmap.samples, pixmap.width, pixmap.height, pixmap.stride, QImage.Format_RGB888)
            pix = QPixmap.fromImage(image)
            self._page_label.setPixmap(pix)
            self._page_label.resize(pix.size())
        except Exception:  # noqa: BLE001
            LOGGER.exception("Failed to render page")

    # -- navigation -----------------------------------------------------------------
    def next_page(self) -> None:
        if self._doc and self._page_index < self._doc.page_count - 1:
            self._page_index += 1
            self._render_page()

    def previous_page(self) -> None:
        if self._doc and self._page_index > 0:
            self._page_index -= 1
            self._render_page()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._close_document()
        super().closeEvent(event)
