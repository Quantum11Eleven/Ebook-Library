from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:  # pragma: no cover - optional dependency
    import fitz  # type: ignore
except Exception:  # pragma: no cover
    fitz = None


class ReaderView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ReaderView")
        self._current_path: str = ""
        self._zoom: float = 1.0
        self._page_widgets: List[QWidget] = []

        top = QHBoxLayout()
        self.btnBack = QPushButton("← Library")
        self.lblTitle = QLabel("(No file)")
        self.btnZoomOut = QPushButton("-")
        self.btnZoomReset = QPushButton("100%")
        self.btnZoomIn = QPushButton("+")
        self.cmbTheme = QComboBox()
        self.cmbTheme.addItems(["Light", "Dark", "Sepia"])
        for widget in (
            self.btnBack,
            self.lblTitle,
            self.btnZoomOut,
            self.btnZoomReset,
            self.btnZoomIn,
            self.cmbTheme,
        ):
            top.addWidget(widget)
        top.addStretch(1)

        splitter = QSplitter()
        self.tabs = QTabWidget()
        self.toc = QTextEdit("Overview / TOC")
        self.tabs.addTab(self.toc, "Overview")
        self.tabs.addTab(QTextEdit("Notes (stub)"), "Notes")

        self.viewerArea = QScrollArea()
        self.viewerArea.setWidgetResizable(True)
        self.viewer = QWidget()
        self.viewerLayout = QVBoxLayout(self.viewer)
        self.viewerLayout.setAlignment(Qt.AlignTop)
        self.viewerArea.setWidget(self.viewer)

        splitter.addWidget(self.tabs)
        splitter.addWidget(self.viewerArea)
        splitter.setStretchFactor(1, 1)

        root = QVBoxLayout(self)
        bar = QWidget()
        bar.setLayout(top)
        root.addWidget(bar)
        root.addWidget(splitter, 1)

        self.btnZoomIn.clicked.connect(lambda: self._set_zoom(self._zoom * 1.1))
        self.btnZoomOut.clicked.connect(lambda: self._set_zoom(self._zoom / 1.1))
        self.btnZoomReset.clicked.connect(lambda: self._set_zoom(1.0))

    def setTitle(self, title: str) -> None:
        self.lblTitle.setText(title)

    def load_pdf(self, path: str, overview_text: str = "") -> None:
        self._current_path = path
        if overview_text:
            self.toc.setPlainText(overview_text)
        self._render_pages()

    def _set_zoom(self, zoom: float) -> None:
        self._zoom = max(0.3, min(3.0, zoom))
        self._render_pages()

    def _clear_viewer(self) -> None:
        for widget in self._page_widgets:
            widget.setParent(None)
            if hasattr(widget, "deleteLater"):
                widget.deleteLater()
        self._page_widgets.clear()

    def _render_pages(self) -> None:
        self._clear_viewer()

        if not self._current_path:
            placeholder = QLabel("No file loaded.")
            self.viewerLayout.addWidget(placeholder)
            self._page_widgets.append(placeholder)
            return

        if fitz is None:
            message = QLabel("PyMuPDF not installed. Run `pip install pymupdf` to enable in-app reading.")
            message.setWordWrap(True)
            self.viewerLayout.addWidget(message)
            self._page_widgets.append(message)
            return

        try:
            doc = fitz.open(self._current_path)
        except Exception as exc:  # pragma: no cover - relies on runtime environment
            error_label = QLabel(f"Failed to open PDF:\n{exc}")
            error_label.setWordWrap(True)
            self.viewerLayout.addWidget(error_label)
            self._page_widgets.append(error_label)
            return

        zoom = self._zoom
        for page in doc:
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            label = QLabel()
            label.setPixmap(QPixmap.fromImage(image))
            self.viewerLayout.addWidget(label)
            self._page_widgets.append(label)
        doc.close()
        spacer = QLabel()
        spacer.setFixedHeight(1)
        self.viewerLayout.addWidget(spacer)
        self._page_widgets.append(spacer)

