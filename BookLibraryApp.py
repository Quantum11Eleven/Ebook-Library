# BookLibraryApp.py
# Single-file PySide6 app:
# - Grid/List views, drag & drop PDFs
# - Double-click or "Read" button -> in-app PDF Reader
# - Details dock with metadata & overview
# - Basic Delete (right-click or via Details)
# Requires: pip install PySide6 pymupdf

from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex, QSize, Signal
from PySide6.QtGui import QAction, QCursor, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

try:  # Optional dependency for PDF rendering
    import fitz  # type: ignore
except Exception:  # pragma: no cover - handled gracefully at runtime
    fitz = None

APP_DIR = Path(__file__).parent
COVERS_DIR = APP_DIR / "covers"
COVERS_DIR.mkdir(parents=True, exist_ok=True)


GENRES = [
    "Astrology & Esoterica",
    "Business, Entrepreneurship & Marketing",
    "Classics & Literature",
    "Contemporary Fiction & YA",
    "Creativity, Art & Making",
    "Driving / DMV (Practical)",
    "Faith, Purpose & Life Design",
    "Health, Longevity & Body",
    "Miscellaneous",
    "Money, Finance & Wealth",
    "Nature, Ecology & Earth-Wisdom",
    "Productivity, Habits & Personal Growth",
    "Psychology & Human Behavior",
    "Relationships, Communication & Attachment",
    "Science, Cosmos & Big Ideas",
    "Self-Love, Confidence & Mindset",
    "Shadow Work, Trauma & Healing",
    "Spirituality, Consciousness & Metaphysics",
]


@dataclass
class Book:
    """Simple in-memory representation of a book in the library."""

    title: str
    author: str = ""
    genre: str = "Miscellaneous"
    path: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cover: Optional[QPixmap] = None
    cover_path: Optional[str] = None
    overview: str = ""
    pages: Optional[int] = None


class BookListModel(QAbstractListModel):
    """Qt model backing the grid view."""

    def __init__(self, items: Optional[List[Book]] = None):
        super().__init__()
        self._items: List[Book] = list(items or [])

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid():
            return None
        book = self._items[index.row()]
        if role == Qt.DisplayRole:
            return f"{book.title}\n{book.author}"
        if role == Qt.DecorationRole:
            pm = None
            if book.cover is not None and not book.cover.isNull():
                pm = book.cover
            elif book.cover_path:
                cover_path = Path(book.cover_path)
                if cover_path.exists():
                    pm = QPixmap(str(cover_path))
            if pm is None or pm.isNull():
                pm = QPixmap(120, 160)
                pm.fill(Qt.darkGray)
            return pm
        return None

    def item(self, row: int) -> Book:
        return self._items[row]

    def add_books(self, books: List[Book]) -> None:
        if not books:
            return
        start = len(self._items)
        self.beginInsertRows(QModelIndex(), start, start + len(books) - 1)
        self._items.extend(books)
        self.endInsertRows()

    def remove_by_id(self, book_id: str) -> bool:
        for i, book in enumerate(self._items):
            if book.id == book_id:
                self.beginRemoveRows(QModelIndex(), i, i)
                self._items.pop(i)
                self.endRemoveRows()
                return True
        return False

    def to_list(self) -> List[Book]:
        return list(self._items)

    def refresh_book(self, book_id: str) -> None:
        for row, book in enumerate(self._items):
            if book.id == book_id:
                idx = self.index(row)
                self.dataChanged.emit(idx, idx, [Qt.DecorationRole, Qt.DisplayRole])
                break


def toast(win: QMainWindow, text: str, ms: int = 2000) -> None:
    win.statusBar().showMessage(text, ms)


def _qimage_from_pixmap_obj(pixmap_obj) -> QImage:
    """Convert a PyMuPDF pixmap to a QImage."""

    return QImage(
        pixmap_obj.samples,
        pixmap_obj.width,
        pixmap_obj.height,
        pixmap_obj.stride,
        QImage.Format_RGB888,
    )


def generate_and_save_cover_from_pdf(
    pdf_path: str,
    out_file: Path,
    thumb_max_w: int = 600,
    thumb_max_h: int = 900,
) -> Optional[Path]:
    """Render the first page of *pdf_path* and save it to *out_file*.

    Returns the written path if successful, otherwise ``None``.
    """

    if fitz is None:
        return None
    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            return None
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        qimg = _qimage_from_pixmap_obj(pix)
        pm = QPixmap.fromImage(qimg)
        pm = pm.scaled(thumb_max_w, thumb_max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        if pm.save(str(out_file), "JPG", quality=92):
            return out_file
        return None
    except Exception:
        return None


def scaled_thumb_from_path(path: Path, width: int = 120, height: int = 160) -> Optional[QPixmap]:
    if not path.exists():
        return None
    pm = QPixmap(str(path))
    if pm.isNull():
        return None
    return pm.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class DragOverlay(QFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet("background: rgba(30,144,255,0.15); border: 2px dashed #1e90ff;")
        self.setVisible(False)
        label = QLabel("Drop PDFs to import\n(Hold Alt to link instead of copy)", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 14px; color: #1e90ff;")
        label.resize(360, 60)
        label.move(40, 40)


class LibraryView(QWidget):
    filesDropped = Signal(list)
    openRequested = Signal(dict)
    selectRequested = Signal(object)
    deleteRequested = Signal(object)

    USERROLE_BOOK = Qt.UserRole + 1

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        self.cmbGenre = QComboBox()
        self.cmbGenre.addItem("All Genres")
        self.cmbGenre.addItems(GENRES)
        self.cmbSort = QComboBox()
        self.cmbSort.addItems(["Sort: Added", "Title", "Author"])
        self.txtSearch = QLineEdit()
        self.txtSearch.setPlaceholderText("Search title/author…")

        fbar = QHBoxLayout()
        fbar.addWidget(self.cmbGenre)
        fbar.addWidget(self.cmbSort)
        fbar.addStretch(1)
        fbar.addWidget(self.txtSearch)

        self.grid = QListView()
        self.grid.setViewMode(QListView.IconMode)
        self.grid.setIconSize(QSize(120, 160))
        self.grid.setResizeMode(QListView.Adjust)
        self.grid.setSpacing(16)
        self.grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self._context_menu_grid)

        self.list = QListWidget()
        self.list.setVisible(False)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._context_menu_list)

        self.model = BookListModel([])
        self.grid.setModel(self.model)

        self.grid.doubleClicked.connect(self._open_from_grid)
        self.grid.clicked.connect(self._select_from_grid)
        self.list.itemDoubleClicked.connect(lambda item: self.openRequested.emit(item.data(Qt.UserRole)))
        self.list.itemClicked.connect(lambda item: self.selectRequested.emit(item.data(self.USERROLE_BOOK)))

        layout = QVBoxLayout(self)
        top = QWidget()
        top.setLayout(fbar)
        layout.addWidget(top)
        layout.addWidget(self.grid, 1)
        layout.addWidget(self.list, 1)

        self.overlay = DragOverlay(self)
        self.overlay.raise_()
        self.txtSearch.textChanged.connect(self._apply_search)

    def toggleMode(self, grid_visible: bool) -> None:
        self.grid.setVisible(grid_visible)
        self.list.setVisible(not grid_visible)

    def populate(self, books: List[Book]) -> None:
        self.model = BookListModel(books)
        self.grid.setModel(self.model)
        self._sync_list_from_model()

    def refresh_book(self, book: Book) -> None:
        self.model.refresh_book(book.id)
        # List entries store the same object reference; nothing else required.

    def _apply_search(self, text: str) -> None:
        lowered = text.strip().lower()
        for i in range(self.list.count()):
            item = self.list.item(i)
            item.setHidden(lowered not in item.text().lower())

    def _sync_list_from_model(self) -> None:
        self.list.clear()
        for book in self.model.to_list():
            item = QListWidgetItem(f"{book.title} — {book.author}")
            item.setData(Qt.UserRole, {"title": book.title, "path": book.path})
            item.setData(self.USERROLE_BOOK, book)
            self.list.addItem(item)

    def _open_from_grid(self, idx: QModelIndex) -> None:
        book = self.model.item(idx.row())
        self.openRequested.emit({"title": book.title, "path": book.path})

    def _select_from_grid(self, idx: QModelIndex) -> None:
        book = self.model.item(idx.row())
        self.selectRequested.emit(book)

    def _context_menu_grid(self, pos) -> None:
        idx = self.grid.indexAt(pos)
        if not idx.isValid():
            return
        book = self.model.item(idx.row())
        self._show_context_menu(book)

    def _context_menu_list(self, pos) -> None:
        item = self.list.itemAt(pos)
        if not item:
            return
        book = item.data(self.USERROLE_BOOK)
        self._show_context_menu(book)

    def _show_context_menu(self, book: Book) -> None:
        menu = QMenu(self)
        act_open = QAction("📖 Read", self)
        act_delete = QAction("🗑️ Delete", self)
        act_open.triggered.connect(lambda: self.openRequested.emit({"title": book.title, "path": book.path}))
        act_delete.triggered.connect(lambda: self.deleteRequested.emit(book))
        menu.addAction(act_open)
        menu.addSeparator()
        menu.addAction(act_delete)
        menu.exec(QCursor.pos())

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    self.overlay.setGeometry(self.rect())
                    self.overlay.setVisible(True)
                    return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:  # type: ignore[override]
        del event  # unused
        self.overlay.setVisible(False)

    def dropEvent(self, event) -> None:  # type: ignore[override]
        self.overlay.setVisible(False)
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile() and url.toLocalFile().lower().endswith(".pdf")
        ]
        if not paths:
            event.ignore()
            return
        books: List[Book] = []
        for pdf_path in paths:
            name = Path(pdf_path).stem
            book = Book(title=name, path=pdf_path)
            cover_target = COVERS_DIR / f"{book.id}.jpg"
            saved = generate_and_save_cover_from_pdf(pdf_path, cover_target)
            if saved is not None:
                book.cover_path = str(saved)
                thumb = scaled_thumb_from_path(saved)
                if thumb is not None:
                    book.cover = thumb
            else:
                pm = QPixmap(120, 160)
                pm.fill(Qt.darkGray)
                book.cover = pm
            books.append(book)
        self.model.add_books(books)
        self._sync_list_from_model()
        self.filesDropped.emit(paths)
        event.acceptProposedAction()


class BookDetailsPanel(QWidget):
    openRequested = Signal(dict)
    deleteRequested = Signal(dict)
    coverChanged = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._book: Optional[Book] = None

        self.lblCover = QLabel()
        self.lblCover.setFixedSize(160, 220)
        self.lblCover.setStyleSheet("border:1px solid #223047; border-radius:6px; background:#222;")

        self.lblTitle = QLabel("—")
        self.lblAuthor = QLabel("—")
        self.lblGenre = QLabel("—")
        self.lblPages = QLabel("—")
        self.lblPath = QLabel("—")

        self.txtOverview = QTextEdit()
        self.txtOverview.setReadOnly(True)
        self.txtOverview.setPlaceholderText("No overview yet…")

        form = QFormLayout()
        form.addRow("Title", self.lblTitle)
        form.addRow("Author", self.lblAuthor)
        form.addRow("Genre", self.lblGenre)
        form.addRow("Pages", self.lblPages)
        form.addRow("File", self.lblPath)

        self.btnRead = QPushButton("📖 Read")
        self.btnChangeCover = QPushButton("Change Cover…")
        self.btnDelete = QPushButton("🗑️ Delete")

        btns = QHBoxLayout()
        btns.addWidget(self.btnRead)
        btns.addWidget(self.btnChangeCover)
        btns.addStretch(1)
        btns.addWidget(self.btnDelete)

        left = QVBoxLayout()
        left.addWidget(self.lblCover, alignment=Qt.AlignTop)
        right = QVBoxLayout()
        right.addLayout(form)
        right.addWidget(QLabel("Overview"))
        right.addWidget(self.txtOverview, 1)
        right.addLayout(btns)

        root = QHBoxLayout(self)
        root.addLayout(left)
        root.addLayout(right, 1)

        self.btnRead.clicked.connect(self._emit_open)
        self.btnChangeCover.clicked.connect(self._change_cover)
        self.btnDelete.clicked.connect(self._emit_delete)

    def show_book(self, book: Book) -> None:
        self._book = book
        pm: Optional[QPixmap] = None
        if book.cover is not None and not book.cover.isNull():
            pm = book.cover
        elif book.cover_path and Path(book.cover_path).exists():
            pm = QPixmap(book.cover_path)
        if pm is None or pm.isNull():
            pm = QPixmap(160, 220)
            pm.fill(Qt.darkGray)
        self.lblCover.setPixmap(pm.scaled(self.lblCover.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.lblTitle.setText(book.title or "—")
        self.lblAuthor.setText(book.author or "—")
        self.lblGenre.setText(book.genre or "—")
        self.lblPages.setText(str(book.pages) if book.pages else "—")
        self.lblPath.setText(book.path or "—")
        self.txtOverview.setPlainText(book.overview or "")

    def _emit_open(self) -> None:
        if not self._book:
            return
        self.openRequested.emit({"path": self._book.path, "title": self._book.title})

    def _emit_delete(self) -> None:
        if not self._book:
            return
        self.deleteRequested.emit({"id": self._book.id, "title": self._book.title})

    def _change_cover(self) -> None:
        if not self._book:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Choose Cover Image", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Invalid image", "Could not load the selected image.")
            return
        dest = COVERS_DIR / f"{self._book.id}.jpg"
        dest.parent.mkdir(parents=True, exist_ok=True)
        normalized = pixmap.scaled(600, 900, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if not normalized.save(str(dest), "JPG", quality=92):
            QMessageBox.warning(self, "Save failed", "Could not save the cover image.")
            return
        thumb = normalized.scaled(120, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._book.cover_path = str(dest)
        self._book.cover = thumb
        self.show_book(self._book)
        self.coverChanged.emit(self._book)


class ReaderView(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        top = QHBoxLayout()
        self.btnBack = QPushButton("← Library")
        self.lblTitle = QLabel("(No file)")
        self.btnZoomOut = QPushButton("-")
        self.btnZoomReset = QPushButton("100%")
        self.btnZoomIn = QPushButton("+")
        self.cmbTheme = QComboBox()
        self.cmbTheme.addItems(["Light", "Dark", "Sepia"])
        for widget in (self.btnBack, self.lblTitle, self.btnZoomOut, self.btnZoomReset, self.btnZoomIn, self.cmbTheme):
            top.addWidget(widget)
        top.addStretch(1)

        splitter = QSplitter()
        self.tabs = QTabWidget()
        self.toc = QTextEdit()
        self.toc.setPlaceholderText("Overview / Table of Contents")
        self.tabs.addTab(self.toc, "Overview/TOC")
        self.tabs.addTab(QTextEdit("Notes (coming soon)"), "Notes")

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

        self._zoom = 1.0
        self._current_path = ""

        self.btnZoomIn.clicked.connect(lambda: self._set_zoom(self._zoom * 1.1))
        self.btnZoomOut.clicked.connect(lambda: self._set_zoom(self._zoom / 1.1))
        self.btnZoomReset.clicked.connect(lambda: self._set_zoom(1.0))

    def setTitle(self, title: str) -> None:
        self.lblTitle.setText(title)

    def load_pdf(self, path: str, overview_text: str = "") -> None:
        self._current_path = path or ""
        if overview_text:
            self.toc.setPlainText(overview_text)
        self._render_pages()

    def _set_zoom(self, zoom: float) -> None:
        self._zoom = max(0.3, min(3.0, zoom))
        self._render_pages()

    def _render_pages(self) -> None:
        while self.viewerLayout.count():
            item = self.viewerLayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not self._current_path:
            self.viewerLayout.addWidget(QLabel("No file loaded."))
            return

        if fitz is None:
            self.viewerLayout.addWidget(QLabel("PyMuPDF not installed.\nRun: pip install pymupdf"))
            return

        try:
            doc = fitz.open(self._current_path)
        except Exception as exc:  # pragma: no cover - runtime feedback
            self.viewerLayout.addWidget(QLabel(f"Failed to open PDF:\n{exc}"))
            return

        for page in doc:
            matrix = fitz.Matrix(self._zoom, self._zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            label = QLabel()
            label.setPixmap(QPixmap.fromImage(image))
            self.viewerLayout.addWidget(label)
        self.viewerLayout.addStretch(1)


class TTSBar(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        self.btnPlay = QPushButton("▶")
        self.btnStop = QPushButton("■")
        self.cmbVoice = QComboBox()
        self.cmbVoice.addItems(["System Default", "Warm Male", "Neutral Female"])
        self.sldSpeed = QSlider(Qt.Horizontal)
        self.sldSpeed.setRange(50, 250)
        self.sldSpeed.setValue(120)
        self.sldPitch = QSlider(Qt.Horizontal)
        self.sldPitch.setRange(-6, 6)
        self.sldPitch.setValue(0)
        self.lblTime = QLabel("00:00")
        for widget in (
            self.btnPlay,
            self.btnStop,
            QLabel("Voice"),
            self.cmbVoice,
            QLabel("Speed"),
            self.sldSpeed,
            QLabel("Pitch"),
            self.sldPitch,
        ):
            layout.addWidget(widget)
        layout.addStretch(1)
        layout.addWidget(self.lblTime)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shelfie — PDF Library")
        self.resize(1200, 780)
        self.statusBar()

        toolbar = QToolBar("Main")
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
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.lstNav = QListWidget()
        dock.setWidget(self.lstNav)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        for text in [
            "All Books",
            "Recently Added",
            "In Progress",
            "Finished",
            "—— Genres ——",
            *GENRES,
        ]:
            item = QListWidgetItem(text)
            if text.startswith("——"):
                item.setFlags(Qt.NoItemFlags)
            self.lstNav.addItem(item)

        self.detailsDock = QDockWidget("Book Details", self)
        self.detailsDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.detailsPanel = BookDetailsPanel()
        self.detailsDock.setWidget(self.detailsPanel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.detailsDock)

        self.library = LibraryView()
        self.reader = ReaderView()
        self.stack = QStackedWidget()
        self.stack.addWidget(self.library)
        self.stack.addWidget(self.reader)
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(8, 8, 8, 8)
        central_layout.addWidget(self.stack)
        self.setCentralWidget(central)

        bottom = QToolBar()
        bottom.setMovable(False)
        bottom.addWidget(TTSBar())
        self.addToolBar(Qt.BottomToolBarArea, bottom)

        self.library.filesDropped.connect(lambda paths: toast(self, f"Imported {len(paths)} PDF(s)"))
        self.library.openRequested.connect(self._open_path_payload)
        self.library.selectRequested.connect(self._show_details)
        self.library.deleteRequested.connect(self._delete_book)
        self.detailsPanel.openRequested.connect(self._open_path_payload)
        self.detailsPanel.deleteRequested.connect(lambda info: self._delete_book_by_id(info["id"], info["title"]))
        self.detailsPanel.coverChanged.connect(self._cover_updated)
        self.lstNav.itemClicked.connect(lambda item: toast(self, f"Filter: {item.text()}"))
        self.actToggleView.triggered.connect(self._toggle_view)
        self.txtSearch.textChanged.connect(self._proxy_search)
        self.reader.btnBack.clicked.connect(lambda: self.stack.setCurrentWidget(self.library))

        self.actImport.triggered.connect(self._choose_files)

    def _proxy_search(self, text: str) -> None:
        self.library.txtSearch.setText(text)

    def _toggle_view(self) -> None:
        grid_visible = self.library.grid.isVisible()
        self.library.toggleMode(not grid_visible)
        toast(self, "View: List" if grid_visible else "View: Grid", 1500)

    def _open_path_payload(self, payload: dict) -> None:
        self._open_path(payload.get("path", ""), payload.get("title", ""))

    def _open_path(self, path: str, title_hint: str = "") -> None:
        if not path:
            toast(self, "No file path.", 2000)
            return
        self.reader.setTitle(title_hint or Path(path).name)
        try:
            self.reader.load_pdf(path, overview_text=self.detailsPanel.txtOverview.toPlainText())
        except Exception as exc:  # pragma: no cover - GUI feedback
            QMessageBox.warning(self, "Open failed", str(exc))
            return
        self.stack.setCurrentWidget(self.reader)
        toast(self, f"Opened: {title_hint or Path(path).name}")

    def _show_details(self, book: Book) -> None:
        self.detailsPanel.show_book(book)

    def _delete_book(self, book: Book) -> None:
        self._confirm_and_delete(book.id, book.title)

    def _delete_book_by_id(self, book_id: str, title: str) -> None:
        self._confirm_and_delete(book_id, title)

    def _cover_updated(self, book: Book) -> None:
        # Update grid/list artwork for the edited book.
        self.library.refresh_book(book)

    def _confirm_and_delete(self, book_id: str, title: str) -> None:
        resp = QMessageBox.question(
            self,
            "Delete Book",
            f"Remove '{title}' from your library?\n(This will NOT delete the file from disk.)",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return
        if self.library.model.remove_by_id(book_id):
            self.library._sync_list_from_model()
            toast(self, f"Deleted: {title}", 2000)
        else:
            toast(self, "Could not find book to delete.", 2000)

    def _choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Import PDFs", "", "PDF Files (*.pdf)")
        if not paths:
            return
        books: List[Book] = []
        for pdf_path in paths:
            name = Path(pdf_path).stem
            book = Book(title=name, path=pdf_path)
            cover_target = COVERS_DIR / f"{book.id}.jpg"
            saved = generate_and_save_cover_from_pdf(pdf_path, cover_target)
            if saved is not None:
                book.cover_path = str(saved)
                thumb = scaled_thumb_from_path(saved)
                if thumb is not None:
                    book.cover = thumb
            else:
                pm = QPixmap(120, 160)
                pm.fill(Qt.darkGray)
                book.cover = pm
            books.append(book)
        self.library.model.add_books(books)
        self.library._sync_list_from_model()
        self.library.filesDropped.emit(paths)


def create_application() -> QApplication:
    return QApplication(sys.argv)


def launch_gui() -> int:
    app = create_application()
    window = MainWindow()
    window.show()
    return app.exec()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="BookLibraryApp")
    parser.add_argument("--headless", action="store_true", help="Do not launch the GUI")
    args = parser.parse_args([] if argv is None else argv)
    if args.headless:
        return 0
    return launch_gui()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
