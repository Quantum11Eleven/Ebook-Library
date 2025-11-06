from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHeaderView,
    QListWidget,
    QTableView,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from shelfie.importers.pipeline import ImportPipeline
from shelfie.models.library_model import LibraryModel


class LibraryView(QWidget):
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

        self._table = QTableView(self)
        self._table.setModel(self._model)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)

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

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._table)
        self.setLayout(layout)

        self._toolbar = QToolBar(self)
        self._toolbar.setMovable(False)
        import_action = QAction("Import PDFs", self)
        import_action.triggered.connect(self._open_import_dialog)
        self._toolbar.addAction(import_action)

    # -- drag and drop --------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        self._pipeline.ingest(paths)
        self._model.refresh()

    # -- actions --------------------------------------------------------------------
    def _open_import_dialog(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Import PDFs", str(Path.home()), "PDF Files (*.pdf)")
        if files:
            self._pipeline.ingest(Path(file) for file in files)
            self._model.refresh()
