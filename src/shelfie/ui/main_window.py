from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QFileDialog,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .dialogs import SettingsDialog
from .details import BookDetailsPanel, BookEditPanel, choose_cover_for
from .library_view import GENRES, Book, LibraryView
from .reader_view import ReaderView
from .tts_bar import TTSBar
from ..utils.repository import LibraryRepositoryJson


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

        self._repo = LibraryRepositoryJson(Path("library.json"))
        loaded_books = [Book.from_dict(payload) for payload in self._repo.load()]
        self.library = LibraryView(initial_books=loaded_books or None)
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
        self.library.bookSelected.connect(self.onBookSelected)
        self.library.libraryChanged.connect(self._persist_library)
        self.actSettings.triggered.connect(self.openSettings)
        self.actImport.triggered.connect(self.openImportDialog)
        self.lstNav.itemClicked.connect(self.onNav)
        self.actToggleView.triggered.connect(self.onToggleView)
        self.txtSearch.textChanged.connect(self._proxySearch)
        self.reader.btnBack.clicked.connect(lambda: self.stack.setCurrentWidget(self.library))

        self.detailsDock = QDockWidget("Book Details", self)
        self.detailsDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.detailsPanel = BookDetailsPanel()
        self.detailsDock.setWidget(self.detailsPanel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.detailsDock)

        self._editPanel: BookEditPanel | None = None
        self._current_book: Book | None = None
        self._covers_dir = Path("covers")

        self.detailsPanel.editRequested.connect(self._begin_edit_book)
        self.detailsPanel.changeCoverRequested.connect(self._change_cover)
        self.detailsPanel.openRequested.connect(lambda payload: self._openPathInReader(payload.get("path", "")))

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

    def _toast(self, message: str, duration: int = 1800) -> None:
        self.statusBar().showMessage(message, duration)

    def onToggleView(self) -> None:
        is_grid_now = self.library.grid.isVisible()
        self.library.toggleMode(not is_grid_now)
        self._toast("View: List" if is_grid_now else "View: Grid")

    def onFilesDropped(self, paths: list) -> None:
        if paths:
            self._toast(f"Imported {len(paths)} PDF(s)")

    def openImportDialog(self) -> None:
        dialog = QFileDialog(self, "Import PDFs")
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilters(["PDF files (*.pdf)", "All files (*.*)"])
        if dialog.exec():
            selected = dialog.selectedFiles()
            books = self.library.import_paths(selected)
            if books:
                last_book = books[-1]
                self._toast(f"Imported {len(books)} PDF(s)")
                self.onBookSelected(last_book)
            else:
                self._toast("No new PDFs imported", 2000)

    def openSettings(self) -> None:
        SettingsDialog(self).exec()

    def onNav(self, item) -> None:
        self._toast(f"Filter: {item.text()}")

    def onOpenBook(self, payload: dict) -> None:
        book = None
        book_id = payload.get("id")
        if book_id:
            book = self.library.get_book_by_id(book_id)
        if not book and payload.get("path"):
            book = self.library.get_book_by_path(payload["path"])
        if book:
            self.onBookSelected(book)
        title = payload.get("title") or (book.title if book else "(Untitled)")
        path = payload.get("path") or (book.path if book else "")
        self.reader.setTitle(title)
        self._openPathInReader(path)
        self._toast(f"Opened: {title}")

    def onBookSelected(self, book: Book) -> None:
        self._current_book = book
        self.detailsPanel.show_book(book.as_dict())

    def _begin_edit_book(self, book_payload: dict) -> None:
        book_id = book_payload.get("id")
        if not book_id:
            return
        book = self.library.get_book_by_id(book_id)
        if not book:
            return
        self._current_book = book
        if self._editPanel is None:
            self._editPanel = BookEditPanel(GENRES, self)
            self._editPanel.saved.connect(self._save_book_edits)
            self._editPanel.canceled.connect(self._restore_details_panel)
        self._editPanel.load_book(book.as_dict())
        self.detailsDock.setWidget(self._editPanel)

    def _restore_details_panel(self) -> None:
        self.detailsDock.setWidget(self.detailsPanel)

    def _save_book_edits(self, updated: dict) -> None:
        book_id = updated.get("id")
        book = self.library.get_book_by_id(book_id) if book_id else self._current_book
        if not book:
            return
        book.title = updated.get("title", book.title)
        book.author = updated.get("author", book.author)
        book.genres = updated.get("genres", book.genres)
        book.publish_date = updated.get("publish_date", book.publish_date)
        book.pages = updated.get("pages", book.pages)
        book.status = updated.get("status", book.status)
        book.path = updated.get("path", book.path)
        book.overview = updated.get("overview", book.overview)
        self.library.model.update_book(book)
        self.library.refresh_views()
        self.detailsPanel.show_book(book.as_dict())
        self._restore_details_panel()
        self._toast("Saved changes.")
        self._persist_library()

    def _change_cover(self, book_payload: dict) -> None:
        book_id = book_payload.get("id")
        if not book_id:
            return
        book = self.library.get_book_by_id(book_id)
        if not book:
            return
        updated = choose_cover_for(book.as_dict(), self._covers_dir)
        cover_path = updated.get("cover_path")
        book.set_cover_from_path(cover_path)
        self.library.model.update_book(book)
        self.library.refresh_views()
        self.detailsPanel.show_book(book.as_dict())
        self._toast("Cover updated.")
        self._persist_library()

    def _openPathInReader(self, path: str) -> None:
        if not path:
            self._toast("No file path to open.", 2000)
            return
        self.stack.setCurrentWidget(self.reader)
        try:
            self.reader.load_pdf(path, overview_text=self.detailsPanel.txtOverview.toPlainText())
        except Exception as exc:  # pragma: no cover - depends on runtime PDF availability
            QMessageBox.warning(self, "Open failed", str(exc))

    def _persist_library(self) -> None:
        try:
            self._repo.save(self.library.all_books())
        except Exception as exc:  # pragma: no cover - filesystem issues are environment-specific
            self._toast(f"Failed to save library: {exc}", 4000)
