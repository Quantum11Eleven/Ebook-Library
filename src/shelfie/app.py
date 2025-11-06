from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from shelfie import database
from shelfie.importers.pipeline import ImportOptions, ImportPipeline
from shelfie.models.library_model import LibraryModel
from shelfie.ui.main_window import MainWindow
from shelfie.ui.reader_view import ReaderView

logging.basicConfig(level=logging.INFO)


def build_application() -> QApplication:
    app = QApplication(sys.argv)
    app.setApplicationName("Shelfie")
    app.setOrganizationName("Shelfie")
    return app


def main() -> int:
    app = build_application()

    conn = database.initialize()
    library_root = Path.home() / "ShelfieLibrary"
    options = ImportOptions(library_root=library_root)
    pipeline = ImportPipeline(conn, options)

    model = LibraryModel(conn)
    reader = ReaderView(pipeline)

    window = MainWindow(model, reader)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
