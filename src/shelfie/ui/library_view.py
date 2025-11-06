from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex, QSize, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from . import resources  # optional icons placeholder
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
    def __init__(self, title: str, author: str, genre: str):
        self.title = title
        self.author = author
        self.genre = genre
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
        self.setStyleSheet(
            "background: rgba(30,144,255,0.15); border: 2px dashed #1e90ff;"
        )
        self.setVisible(False)
        label = QLabel("Drop PDFs to import\n(Hold Alt to Link instead of Copy)", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 14px; color: #1e90ff;")
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.resize(360, 60)
        label.move(40, 40)


class LibraryView(QWidget):
    filesDropped = Signal(list)

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

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.cmbGenre)
        filter_layout.addWidget(self.cmbSort)
        filter_layout.addStretch(1)
        filter_layout.addWidget(self.txtSearch)

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
                Book("Metaphysics 101", "A. Mystic", "Spirituality, Consciousness & Metaphysics"),
            ]
        )
        self.grid.setModel(self.model)

        layout = QVBoxLayout(self)
        filters_widget = QWidget()
        filters_widget.setLayout(filter_layout)
        layout.addWidget(filters_widget)
        layout.addWidget(self.grid, 1)

        self.overlay = DragOverlay(self)
        self.overlay.raise_()

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
        event.accept()

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
