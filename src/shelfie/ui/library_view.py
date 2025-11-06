from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from shelfie.importers.pipeline import ImportPipeline
from shelfie.models.library_model import LibraryModel


class LibraryView(QWidget):
    """Library browsing surface with list/grid modes and drag-and-drop import."""

    book_open_requested = Signal(Path)

    def __init__(
        self,
        model: LibraryModel,
        pipeline: ImportPipeline,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._model = model
        self._pipeline = pipeline

        self.setAcceptDrops(True)

        self._import_action = QAction("Import PDFs", self)
        self._import_action.setShortcut("Ctrl+I")
        self._import_action.triggered.connect(self.open_import_dialog)
        self.addAction(self._import_action)

        self._table = QTableView(self)
        self._table.setModel(self._model)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.doubleClicked.connect(self._open_from_index)

        self._grid = QListWidget(self)
        self._grid.setViewMode(QListWidget.IconMode)
        self._grid.setResizeMode(QListWidget.Adjust)
        self._grid.setWordWrap(True)
        self._grid.itemActivated.connect(self._open_from_item)

        self._stack = QStackedWidget(self)
        self._stack.addWidget(self._table)
        self._stack.addWidget(self._grid)

        self._sidebar = QListWidget(self)
        self._sidebar.addItems(
            [
                "Library",
                "Recently Added",
                "In Progress",
                "Finished",
            ]
        )
        self._sidebar.setMaximumWidth(180)

        splitter = QSplitter(self)
        splitter.addWidget(self._sidebar)
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        self.setLayout(layout)

        self._model.modelReset.connect(self._populate_grid)
        self._populate_grid()

    # -- public API ---------------------------------------------------------
    @property
    def import_action(self) -> QAction:
        return self._import_action

    def set_view_mode(self, mode: str) -> None:
        self._stack.setCurrentIndex(1 if mode == "grid" else 0)

    def set_search_text(self, text: str) -> None:
        self._model.set_search_text(text)

    def set_genre_filter(self, genre_id: int | None) -> None:
        self._model.set_genre_filter(genre_id)

    def open_import_dialog(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Import PDFs",
            str(Path.home()),
            "PDF Files (*.pdf)",
        )
        if files:
            self.import_paths(Path(file) for file in files)

    def import_paths(self, paths: Iterable[Path]) -> None:
        normalized = [Path(p) for p in paths]
        if not normalized:
            return
        self._pipeline.ingest(normalized)
        self._model.refresh()

    # -- Qt events ---------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        self.import_paths(paths)

    # -- helpers ------------------------------------------------------------
    def _populate_grid(self) -> None:
        self._grid.clear()
        for row in range(self._model.rowCount()):
            record = self._model.book_at(self._model.index(row, 0))
            if record is None:
                continue
            item = QListWidgetItem(record.title)
            decoration = self._model.data(self._model.index(row, 0), Qt.DecorationRole)
            if decoration:
                item.setIcon(decoration)
            item.setData(Qt.UserRole, record)
            item.setToolTip(f"{record.title}\n{record.author or 'Unknown author'}")
            self._grid.addItem(item)

    def _open_from_index(self, index) -> None:  # type: ignore[override]
        record = self._model.book_at(index)
        if record:
            self.book_open_requested.emit(record.file_path)

    def _open_from_item(self, item: QListWidgetItem) -> None:
        record = item.data(Qt.UserRole)
        if record:
            self.book_open_requested.emit(record.file_path)
