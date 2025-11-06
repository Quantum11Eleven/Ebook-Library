from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QMainWindow,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from shelfie.models.library_model import BookRecord, LibraryModel
from shelfie.ui.library_view import LibraryView
from shelfie.ui.reader_view import ReaderView


class MainWindow(QMainWindow):
    def __init__(self, model: LibraryModel, reader: ReaderView, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Shelfie")
        self.resize(1280, 800)

        self._stack = QStackedWidget(self)
        self._library_view = LibraryView(model, reader.pipeline)
        self._library_view.book_open_requested.connect(self._on_book_open_requested)
        self._stack.addWidget(self._library_view)
        self._stack.addWidget(reader)

        self._reader = reader
        self._model = model
        self._reader.reading_state_updated.connect(self._model.refresh)

        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)
        self.setCentralWidget(central_widget)

        toolbar = QToolBar("Shelfie Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        library_action = QAction("Library", self)
        library_action.setCheckable(True)
        library_action.setChecked(True)
        library_action.triggered.connect(lambda: self._stack.setCurrentIndex(0))

        reader_action = QAction("Reader", self)
        reader_action.setCheckable(True)
        reader_action.triggered.connect(lambda: self._stack.setCurrentIndex(1))

        view_group = QActionGroup(self)
        view_group.addAction(library_action)
        view_group.addAction(reader_action)
        view_group.setExclusive(True)

        toolbar.addAction(library_action)
        toolbar.addAction(reader_action)

        toolbar.addSeparator()
        toolbar.addAction(self._library_view.import_action)

        toolbar.addSeparator()

        self._view_toggle = QActionGroup(self)
        list_action = QAction("List View", self)
        list_action.setCheckable(True)
        list_action.setChecked(True)
        list_action.triggered.connect(lambda: self._library_view.set_view_mode("list"))
        grid_action = QAction("Grid View", self)
        grid_action.setCheckable(True)
        grid_action.triggered.connect(lambda: self._library_view.set_view_mode("grid"))
        self._view_toggle.addAction(list_action)
        self._view_toggle.addAction(grid_action)
        self._view_toggle.setExclusive(True)
        toolbar.addActions(self._view_toggle.actions())

        toolbar.addSeparator()

        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Search library…")
        self._search.textChanged.connect(self._library_view.set_search_text)
        toolbar.addWidget(self._search)

        self._genre_selector = QComboBox(self)
        self._genre_selector.addItem("All Genres", userData=None)
        for genre_id, name in model.genres():
            self._genre_selector.addItem(name, userData=genre_id)
        self._genre_selector.currentIndexChanged.connect(self._on_genre_changed)
        toolbar.addWidget(self._genre_selector)

    def _on_genre_changed(self, index: int) -> None:
        genre_id = self._genre_selector.itemData(index)
        self._library_view.set_genre_filter(genre_id)

    def _on_book_open_requested(self, record: BookRecord) -> None:
        self._reader.open_book(record)
        self._stack.setCurrentIndex(1)

    @property
    def library_view(self) -> LibraryView:
        return self._library_view

    @property
    def stack(self) -> QStackedWidget:
        return self._stack
