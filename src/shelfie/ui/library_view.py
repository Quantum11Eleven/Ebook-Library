from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional
from uuid import uuid4

from PySide6.QtCore import QAbstractListModel, QModelIndex, QSize, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..utils.importing import collect_pdf_paths

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


def _placeholder_cover(width: int = 120, height: int = 160) -> QPixmap:
    pixmap = QPixmap(width, height)
    fill = getattr(pixmap, "fill", None)
    colour = getattr(Qt, "darkGray", None)
    if callable(fill) and colour is not None:
        fill(colour)
    return pixmap


@dataclass
class Book:
    title: str
    author: str
    genres: list[str] = field(default_factory=lambda: ["Miscellaneous"])
    path: str = ""
    overview: str = ""
    publish_date: str = ""
    pages: Optional[int] = None
    tags: list[str] = field(default_factory=list)
    rating: Optional[int] = None
    status: str = "Unread"
    cover_path: Optional[str] = None
    added_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds"))
    custom: dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid4().hex)
    cover: QPixmap = field(default_factory=_placeholder_cover)

    @property
    def genre(self) -> str:
        if self.genres:
            return self.genres[0]
        return "Miscellaneous"

    def set_cover_from_path(self, path: Optional[str]) -> None:
        self.cover_path = path
        pixmap: QPixmap
        if path:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(QSize(120, 160), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                pixmap = _placeholder_cover()
        else:
            pixmap = _placeholder_cover()
        self.cover = pixmap

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "genres": list(self.genres),
            "overview": self.overview,
            "publish_date": self.publish_date,
            "pages": self.pages,
            "tags": list(self.tags),
            "rating": self.rating,
            "status": self.status,
            "path": self.path,
            "cover_path": self.cover_path,
            "added_at": self.added_at,
            "custom": dict(self.custom),
        }


class BookListModel(QAbstractListModel):
    def __init__(self, items=None):
        super().__init__()
        self._items: list[Book] = items or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def data(self, index, role):
        if not index.isValid():
            return None
        book = self._items[index.row()]
        if role == Qt.DisplayRole:
            return f"{book.title}\n{book.author}"
        if role == Qt.DecorationRole:
            return book.cover
        return None

    def item(self, row: int) -> Book:
        return self._items[row]

    def addBooks(self, books):
        if not books:
            return
        start = len(self._items)
        self.beginInsertRows(QModelIndex(), start, start + len(books) - 1)
        self._items.extend(books)
        self.endInsertRows()

    def contains_path(self, path: str) -> bool:
        if not path:
            return False
        return any(getattr(book, "path", None) == path for book in self._items)

    def find_by_id(self, book_id: str) -> Optional[Book]:
        for book in self._items:
            if book.id == book_id:
                return book
        return None

    def find_by_path(self, path: str) -> Optional[Book]:
        for book in self._items:
            if book.path == path:
                return book
        return None

    def update_book(self, updated: Book) -> None:
        for index, book in enumerate(self._items):
            if book.id == updated.id:
                self._items[index] = updated
                top_left = self.index(index)
                self.dataChanged.emit(top_left, top_left, [Qt.DisplayRole, Qt.DecorationRole])
                break


class DragOverlay(QFrame):
    def __init__(self, parent=None):
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
    bookSelected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LibraryView")
        self.setAcceptDrops(True)

        self.cmbGenre = QComboBox()
        self.cmbGenre.addItem("All Genres")
        self.cmbGenre.addItems(GENRES)
        self.cmbSort = QComboBox()
        self.cmbSort.addItems(["Sort: Added", "Title", "Author"])
        self.txtSearch = QLineEdit()
        self.txtSearch.setPlaceholderText("Search title/author…")
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(self.cmbGenre)
        filter_bar.addWidget(self.cmbSort)
        filter_bar.addStretch(1)
        filter_bar.addWidget(self.txtSearch)

        self.grid = QListView()
        self.grid.setViewMode(QListView.IconMode)
        self.grid.setIconSize(QSize(120, 160))
        self.grid.setResizeMode(QListView.Adjust)
        self.grid.setSpacing(16)
        self.model = BookListModel(
            [
                Book(
                    title="Your First 1000 Copies",
                    author="Tim Grahl",
                    genres=["Business, Entrepreneurship & Marketing"],
                ),
                Book(
                    title="Metaphysics 101",
                    author="A. Mystic",
                    genres=["Spirituality, Consciousness & Metaphysics"],
                ),
            ]
        )
        for book in self.model._items:
            book.set_cover_from_path(book.cover_path)
        self.grid.setModel(self.model)
        self.grid.doubleClicked.connect(self._on_open)
        self.grid.clicked.connect(self._on_selected)

        self.list = QListWidget()
        self._sync_list_from_model()
        self.list.itemDoubleClicked.connect(lambda item: self.openRequested.emit(item.data(Qt.UserRole)))
        self.list.itemClicked.connect(self._on_item_clicked)
        self.list.setVisible(False)

        layout = QVBoxLayout(self)
        filters_widget = QWidget()
        filters_widget.setLayout(filter_bar)
        layout.addWidget(filters_widget)
        layout.addWidget(self.grid, 1)
        layout.addWidget(self.list, 1)

        self.overlay = DragOverlay(self)
        self.overlay.raise_()

        self._wire_search()

    def toggleMode(self, grid: bool) -> None:
        self.grid.setVisible(grid)
        self.list.setVisible(not grid)

    def _apply_search(self, text: str) -> None:
        query = text.strip().lower()
        for index in range(self.list.count()):
            item = self.list.item(index)
            item.setHidden(query not in item.text().lower())

    def _sync_list_from_model(self) -> None:
        self.list.clear()
        for row in range(self.model.rowCount()):
            book = self.model.item(row)
            item = QListWidgetItem(f"{book.title} — {book.author}")
            item.setData(Qt.UserRole, {"id": book.id, "title": book.title, "path": getattr(book, "path", "")})
            self.list.addItem(item)

    def _on_open(self, index):
        book = self.model.item(index.row())
        self.openRequested.emit({"id": book.id, "title": book.title, "path": book.path})

    def _on_selected(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        book = self.model.item(index.row())
        self.bookSelected.emit(book)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        payload = item.data(Qt.UserRole)
        if not payload:
            return
        book_id = payload.get("id")
        book = self.model.find_by_id(book_id) if book_id else None
        if book:
            self.bookSelected.emit(book)

    def _wire_search(self) -> None:
        self.txtSearch.textChanged.connect(self._apply_search)

    def import_paths(self, paths: Iterable[str]) -> list[Book]:
        normalized = collect_pdf_paths(paths)
        unique_paths: list[str] = []
        for candidate in normalized:
            if self.model.contains_path(candidate):
                continue
            unique_paths.append(candidate)

        books: list[Book] = []
        for path in unique_paths:
            title = Path(path).stem or "(Untitled)"
            book = Book(title=title, author="", genres=["Miscellaneous"], path=path)
            book.set_cover_from_path(None)
            books.append(book)

        if not books:
            return []

        self.model.addBooks(books)
        self._sync_list_from_model()
        self._apply_search(self.txtSearch.text())
        self.filesDropped.emit(unique_paths)
        return books

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                local_path = url.toLocalFile()
                if not url.isLocalFile():
                    continue
                path_obj = Path(local_path)
                if path_obj.is_dir() or local_path.lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    self.overlay.setGeometry(self.rect())
                    self.overlay.setVisible(True)
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.overlay.setVisible(False)

    def dropEvent(self, event: QDropEvent):
        self.overlay.setVisible(False)
        raw_paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]
        books = self.import_paths(raw_paths)
        if not books:
            event.ignore()
            return
        last_book = books[-1]
        self.bookSelected.emit(last_book)
        self.openRequested.emit({"id": last_book.id, "title": last_book.title, "path": last_book.path})
        event.acceptProposedAction()

    def get_book_by_id(self, book_id: str) -> Optional[Book]:
        return self.model.find_by_id(book_id)

    def get_book_by_path(self, path: str) -> Optional[Book]:
        return self.model.find_by_path(path)

    def refresh_views(self) -> None:
        self._sync_list_from_model()
        self._apply_search(self.txtSearch.text())
