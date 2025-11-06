from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMainWindow,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..utils.signals import app_signals
from .dialogs import SettingsDialog
from .library_view import GENRES, LibraryView
from .reader_view import ReaderView
from .tts_bar import TTSBar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("Shelfie — PDF Library")
        self.resize(1200, 780)

        self._load_styles()

        toolbar = QToolBar("tbMain")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.actMenu = QAction("☰", self)
        self.actImport = QAction("Import", self)
        self.actToggleView = QAction("Grid/List", self)
        self.actSettings = QAction("⚙", self)
        self.txtSearch = QLineEdit()
        self.txtSearch.setPlaceholderText("Search…")
        for action in (self.actMenu, self.actImport, self.actToggleView, self.actSettings):
            toolbar.addAction(action)
        toolbar.addSeparator()
        toolbar.addWidget(self.txtSearch)

        dock = QDockWidget("Library", self)
        dock.setObjectName("dockSidebar")
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.lstNav = QListWidget()
        dock.setWidget(self.lstNav)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        for item in [
            "All Books",
            "Recently Added",
            "In Progress",
            "Finished",
            "—— Genres ——",
        ] + GENRES:
            list_item = QListWidgetItem(item)
            if item.startswith("——"):
                list_item.setFlags(Qt.NoItemFlags)
            self.lstNav.addItem(list_item)

        self.library = LibraryView()
        self.reader = ReaderView()
        self.stack = QStackedWidget()
        self.stack.addWidget(self.library)
        self.stack.addWidget(self.reader)
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.stack)
        self.setCentralWidget(central)

        self.tts = TTSBar()
        self.statusBar()
        self.addToolBarBreak()
        self.addToolBar(Qt.BottomToolBarArea, self._wrap_bottom(self.tts))

        self.library.filesDropped.connect(self.onFilesDropped)
        self.library.openRequested.connect(self.onOpenBook)
        app_signals.showToast.connect(self.statusBar().showMessage)
        self.actSettings.triggered.connect(self.openSettings)
        self.lstNav.itemClicked.connect(self.onNav)
        self.actToggleView.triggered.connect(self.onToggleView)
        self.txtSearch.textChanged.connect(self._proxySearch)
        self.reader.btnBack.clicked.connect(lambda: self.stack.setCurrentWidget(self.library))

        self.actImport.setShortcut("Ctrl+O")
        self.txtSearch.setClearButtonEnabled(True)

    def _load_styles(self) -> None:
        style_path = Path(__file__).with_name("styles.qss")
        try:
            self.setStyleSheet(style_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            pass

    def _wrap_bottom(self, widget: QWidget) -> QToolBar:
        bar = QToolBar()
        bar.setMovable(False)
        bar.addWidget(widget)
        return bar

    def _proxySearch(self, text: str) -> None:
        self.library.txtSearch.setText(text)

    def onToggleView(self) -> None:
        is_grid_now = self.library.grid.isVisible()
        self.library.toggleMode(not is_grid_now)
        self.statusBar().showMessage("View: List" if is_grid_now else "View: Grid", 2000)

    def onFilesDropped(self, paths: list) -> None:
        if paths:
            self.statusBar().showMessage(f"Queued {len(paths)} PDF(s) for import…", 2000)

    def openSettings(self) -> None:
        SettingsDialog(self).exec()

    def onNav(self, item) -> None:
        self.statusBar().showMessage(f"Filter: {item.text()}", 2500)

    def onOpenBook(self, payload: dict) -> None:
        title = payload.get("title", "(Untitled)")
        self.reader.setTitle(title)
        self.stack.setCurrentWidget(self.reader)
        self.statusBar().showMessage(f"Opened: {title}", 2500)
