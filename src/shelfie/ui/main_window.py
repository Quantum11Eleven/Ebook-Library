from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QToolBar, QVBoxLayout, QWidget

from shelfie.models.library_model import LibraryModel
from shelfie.ui.library_view import LibraryView
from shelfie.ui.reader_view import ReaderView


class MainWindow(QMainWindow):
    def __init__(self, model: LibraryModel, reader: ReaderView, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Shelfie")
        self.resize(1280, 800)

        self._stack = QStackedWidget(self)
        self._library_view = LibraryView(model, reader.pipeline)
        self._stack.addWidget(self._library_view)
        self._stack.addWidget(reader)

        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)
        self.setCentralWidget(central_widget)

        toolbar = QToolBar("Shelfie Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        library_action = QAction("Library", self)
        library_action.triggered.connect(lambda: self._stack.setCurrentIndex(0))
        toolbar.addAction(library_action)

        reader_action = QAction("Reader", self)
        reader_action.triggered.connect(lambda: self._stack.setCurrentIndex(1))
        toolbar.addAction(reader_action)

        self._search_action = QAction("Search", self)
        toolbar.addAction(self._search_action)

    @property
    def library_view(self) -> LibraryView:
        return self._library_view

    @property
    def stack(self) -> QStackedWidget:
        return self._stack
