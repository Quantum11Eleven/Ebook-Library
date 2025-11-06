from pathlib import Path

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


class Book:
    def __init__(self, title: str, author: str, genre: str, path: str = ""):
        self.title = title
        self.author = author
        self.genre = genre
        self.path = path
        self.cover = QPixmap(120, 160)
        self.cover.fill(Qt.darkGray)


class BookListModel(QAbstractListModel):
    def __init__(self, items=None):
        super().__init__()
        self._items = items or []

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
                    "Your First 1000 Copies",
                    "Tim Grahl",
                    "Business, Entrepreneurship & Marketing",
                ),
                Book(
                    "Metaphysics 101",
                    "A. Mystic",
                    "Spirituality, Consciousness & Metaphysics",
                ),
            ]
        )
        self.grid.setModel(self.model)
        self.grid.doubleClicked.connect(self._on_open)

        self.list = QListWidget()
        self._sync_list_from_model()
        self.list.itemDoubleClicked.connect(lambda item: self.openRequested.emit(item.data(Qt.UserRole)))
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
            item.setData(Qt.UserRole, {"title": book.title, "path": getattr(book, "path", "")})
            self.list.addItem(item)

    def _on_open(self, index):
        book = self.model.item(index.row())
        self.openRequested.emit({"title": book.title, "path": book.path})

    def _wire_search(self) -> None:
        self.txtSearch.textChanged.connect(self._apply_search)

    def import_paths(self, paths: list[str]) -> list[Book]:
        unique_paths = []
        for path in paths:
            if not path:
                continue
            if self.model.contains_path(path):
                continue
            unique_paths.append(path)

        books = []
        for path in unique_paths:
            title = Path(path).stem or "(Untitled)"
            books.append(Book(title, "", "Miscellaneous", path))

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
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    self.overlay.setGeometry(self.rect())
                    self.overlay.setVisible(True)
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.overlay.setVisible(False)

    def dropEvent(self, event: QDropEvent):
        self.overlay.setVisible(False)
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile() and url.toLocalFile().lower().endswith(".pdf")
        ]
        if not paths:
            event.ignore()
            return

        books = self.import_paths(paths)
        if books:
            last_book = books[-1]
            self.openRequested.emit({"title": last_book.title, "path": last_book.path})

        event.acceptProposedAction()
