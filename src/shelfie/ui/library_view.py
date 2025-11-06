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

from ..utils.signals import app_signals

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
        start = len(self._items)
        if not books:
            return
        self.beginInsertRows(QModelIndex(), start, start + len(books) - 1)
        self._items.extend(books)
        self.endInsertRows()


class DragOverlay(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: rgba(30,144,255,0.15); border: 2px dashed #1e90ff;")
        self.setVisible(False)
        label = QLabel("Drop PDFs to import\n(Hold Alt to Link instead of Copy)", self)
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
        for i in range(self.model.rowCount()):
            book = self.model.item(i)
            item = QListWidgetItem(f"{book.title} — {book.author}")
            item.setData(Qt.UserRole, {"title": book.title, "path": getattr(book, "path", "")})
            self.list.addItem(item)
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

    def _on_open(self, index):
        book = self.model.item(index.row())
        self.openRequested.emit({"title": book.title, "path": book.path})

    def _wire_search(self) -> None:
        def apply():
            text = self.txtSearch.text().strip().lower()
            for i in range(self.list.count()):
                item = self.list.item(i)
                item.setHidden(text not in item.text().lower())

        self.txtSearch.textChanged.connect(apply)

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
        if paths:
            self.filesDropped.emit(paths)
            app_signals.showToast.emit(f"Queued {len(paths)} PDF(s) for import…")
            event.acceptProposedAction()
        else:
            event.ignore()
