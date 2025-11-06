from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .dialogs import SettingsDialog
from .library_view import GENRES, LibraryView
from .reader_view import ReaderView
from .tts_bar import TTSBar
from ..utils.signals import app_signals


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("Shelfie — PDF Library")
        self.resize(1100, 720)

        toolbar = QToolBar("tbMain")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.actMenu = QAction("\u2630", self)
        self.actImport = QAction("Import", self)
        self.actToggleView = QAction("Grid/List", self)
        self.actSettings = QAction("\u2699", self)

        toolbar.addAction(self.actMenu)
        toolbar.addAction(self.actImport)
        toolbar.addAction(self.actToggleView)
        toolbar.addAction(self.actSettings)

        toolbar.addSeparator()
        self.txtSearch = QLineEdit()
        self.txtSearch.setPlaceholderText("Search…")
        toolbar.addWidget(self.txtSearch)

        dock = QDockWidget("Library", self)
        dock.setObjectName("dockSidebar")
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.lstNav = QListWidget()
        dock.setWidget(self.lstNav)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        for item_text in [
            "All Books",
            "Recently Added",
            "In Progress",
            "Finished",
            "—— Genres ——",
            *GENRES,
        ]:
            item = QListWidgetItem(item_text)
            if item_text.startswith("——"):
                item.setFlags(Qt.NoItemFlags)
            self.lstNav.addItem(item)

        self.library = LibraryView()
        self.reader = ReaderView()

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.addWidget(self.library)
        self.setCentralWidget(central)

        self.tts = TTSBar()
        self.statusBar()
        self.addToolBarBreak()
        self.addToolBar(Qt.BottomToolBarArea, self._wrap_bottom(self.tts))

        self.library.filesDropped.connect(self.on_files_dropped)
        app_signals.showToast.connect(self.statusBar().showMessage)
        self.actSettings.triggered.connect(self.open_settings)
        self.lstNav.itemClicked.connect(self.on_nav)

        self.actImport.setShortcut("Ctrl+O")
        self.txtSearch.setClearButtonEnabled(True)

    def _wrap_bottom(self, widget: QWidget) -> QToolBar:
        bar = QToolBar()
        bar.setMovable(False)
        bar.addWidget(widget)
        return bar

    def on_files_dropped(self, paths: list[str]) -> None:
        QMessageBox.information(self, "Import", f"Pretend importing {len(paths)} PDF(s)…")

    def open_settings(self) -> None:
        SettingsDialog(self).exec()

    def on_nav(self, item: QListWidgetItem) -> None:
        self.statusBar().showMessage(f"Filter: {item.text()}", 2500)
