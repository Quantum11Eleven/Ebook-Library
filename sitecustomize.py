"""Provide stub implementations for optional third-party modules.

This allows the project test suite to run in environments where PySide6,
PyMuPDF (fitz), or Pillow are unavailable by supplying lightweight stand-ins
that implement the limited interfaces exercised by the tests.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _install_pyside6_stub() -> None:
    if importlib.util.find_spec("PySide6") is not None:
        return

    pkg = types.ModuleType("PySide6")
    pkg.__path__ = []  # type: ignore[attr-defined]
    sys.modules.setdefault("PySide6", pkg)

    # --- QtCore -----------------------------------------------------------------
    qtcore = types.ModuleType("PySide6.QtCore")

    class Qt:
        DisplayRole = 0
        EditRole = 1
        UserRole = 32
        Horizontal = 1
        Vertical = 2
        TopToolBarArea = 0
        AlignCenter = 0x84
        AlignTop = 0x20
        KeepAspectRatio = 0x01
        SmoothTransformation = 0x02
        darkGray = 0x404040

    class QObject:
        def __init__(self, parent: object | None = None) -> None:
            self._parent = parent

    class Signal:
        def __init__(self, *signature: object) -> None:
            self._name: str | None = None

        def __set_name__(self, owner: type, name: str) -> None:
            self._name = f"__qt_signal_{name}"

        def __get__(self, instance: object | None, owner: type | None = None) -> object:
            if instance is None:
                return self

            slots = instance.__dict__.setdefault(self._name, [])  # type: ignore[arg-type]

            def connect(slot):
                slots.append(slot)

            def emit(*args, **kwargs):
                for slot in list(slots):
                    slot(*args, **kwargs)

            return types.SimpleNamespace(connect=connect, emit=emit)

    class QModelIndex:
        def __init__(self, row: int = -1, column: int = -1) -> None:
            self._row = row
            self._column = column

        def isValid(self) -> bool:
            return self._row >= 0 and self._column >= 0

        def row(self) -> int:
            return self._row

        def column(self) -> int:
            return self._column

    class QSize:
        def __init__(self, width: int, height: int) -> None:
            self._width = width
            self._height = height

        def width(self) -> int:
            return self._width

        def height(self) -> int:
            return self._height

    class QAbstractTableModel(QObject):
        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)

        def rowCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
            return 0

        def columnCount(self, parent: QModelIndex | None = None) -> int:  # noqa: N802
            return 0

        def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> object:  # noqa: N802
            return None

        def headerData(self, section: int, orientation: int, role: int = Qt.DisplayRole) -> object:  # noqa: N802
            return None

        def beginResetModel(self) -> None:
            pass

        def endResetModel(self) -> None:
            pass

    class QAbstractListModel(QAbstractTableModel):
        def index(self, row: int, column: int = 0, parent: QModelIndex | None = None) -> QModelIndex:  # noqa: N802
            return QModelIndex(row, column)

    qtcore.Qt = Qt
    qtcore.QObject = QObject
    qtcore.Signal = Signal
    qtcore.QModelIndex = QModelIndex
    qtcore.QSize = QSize
    qtcore.QAbstractTableModel = QAbstractTableModel
    qtcore.QAbstractListModel = QAbstractListModel
    sys.modules["PySide6.QtCore"] = qtcore
    pkg.QtCore = qtcore

    # --- QtWidgets --------------------------------------------------------------
    qtwidgets = types.ModuleType("PySide6.QtWidgets")

    class QWidget(QObject):
        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._layout = None
            self._parent_widget = parent

        def setAcceptDrops(self, _enabled: bool) -> None:
            pass

        def setLayout(self, layout) -> None:
            self._layout = layout

        def layout(self):
            return self._layout

        def setFixedSize(self, _w: int, _h: int) -> None:
            pass

        def setFixedHeight(self, _h: int) -> None:
            pass

        def setParent(self, parent: object | None) -> None:
            self._parent_widget = parent

        def parent(self) -> object | None:
            return self._parent_widget

        def deleteLater(self) -> None:
            pass

    class QFrame(QWidget):
        pass

    class QApplication(QObject):
        _instance: "QApplication | None" = None

        def __init__(self, args: list[str] | None = None) -> None:
            super().__init__(None)
            QApplication._instance = self
            self.args = args or []

        @staticmethod
        def instance() -> "QApplication | None":
            return QApplication._instance

        def exec(self) -> int:
            return 0

        def setApplicationName(self, _name: str) -> None:
            pass

        def setOrganizationName(self, _name: str) -> None:
            pass

    class _LayoutItem:
        def __init__(self, widget: object | None = None, layout: object | None = None) -> None:
            self._widget = widget
            self._layout = layout

        def widget(self) -> object | None:
            return self._widget

        def layout(self) -> object | None:
            return self._layout

    class QVBoxLayout:
        def __init__(self, parent: object | None = None) -> None:
            self._parent = parent
            self._children: list[_LayoutItem] = []
            self._alignment = None

        def setContentsMargins(self, *args: object) -> None:
            pass

        def addWidget(self, widget: object, stretch: int | None = None) -> None:
            self._children.append(_LayoutItem(widget=widget))

        def addLayout(self, layout: object, stretch: int | None = None) -> None:
            self._children.append(_LayoutItem(layout=layout))

        def addStretch(self, _stretch: int = 0) -> None:
            self._children.append(_LayoutItem())

        def setAlignment(self, alignment: int) -> None:
            self._alignment = alignment

        def count(self) -> int:
            return len(self._children)

        def takeAt(self, index: int) -> _LayoutItem | None:
            if 0 <= index < len(self._children):
                return self._children.pop(index)
            return None

        def itemAt(self, index: int) -> _LayoutItem | None:
            if 0 <= index < len(self._children):
                return self._children[index]
            return None

    class QHBoxLayout(QVBoxLayout):
        def addSpacing(self, _size: int) -> None:
            pass

        def addItem(self, item: object) -> None:
            self._children.append(_LayoutItem(widget=item))

    class QStackedWidget(QWidget):
        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._widgets: list[object] = []
            self._current_index = 0

        def addWidget(self, widget: object) -> None:
            self._widgets.append(widget)

        def setCurrentIndex(self, index: int) -> None:
            self._current_index = index

    class QMainWindow(QWidget):
        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._central_widget = None

        def setWindowTitle(self, _title: str) -> None:
            pass

        def resize(self, _w: int, _h: int) -> None:
            pass

        def addToolBar(self, _area: int, _toolbar: object) -> None:
            pass

        def setCentralWidget(self, widget: object) -> None:
            self._central_widget = widget

        def show(self) -> None:
            pass

    class QHeaderView:
        Stretch = 1

        def setSectionResizeMode(self, _mode: int) -> None:
            pass

    class QAbstractItemView:
        SelectRows = 1
        SingleSelection = 1

    class QTableView(QWidget):
        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._model = None
            self._header = QHeaderView()

        def setModel(self, model: object) -> None:
            self._model = model

        def horizontalHeader(self) -> QHeaderView:
            return self._header

        def setSelectionBehavior(self, _mode: int) -> None:
            pass

        def setSelectionMode(self, _mode: int) -> None:
            pass

    class QListWidgetItem:
        def __init__(self, text: str = "") -> None:
            self._text = text
            self._data: dict[int, object] = {}
            self._flags = True
            self._hidden = False

        def setFlags(self, flags: object) -> None:
            self._flags = bool(flags)

        def setData(self, role: int, value: object) -> None:
            self._data[role] = value

        def data(self, role: int) -> object | None:
            return self._data.get(role)

        def text(self) -> str:
            return self._text

        def setHidden(self, hidden: bool) -> None:
            self._hidden = hidden

    class QListWidget(QWidget):
        itemDoubleClicked = qtcore.Signal(object)
        itemClicked = qtcore.Signal(object)
        customContextMenuRequested = qtcore.Signal(object)

        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._items: list[QListWidgetItem] = []
            self._max_width = None
            self._visible = True
            self._context_policy = None

        def addItems(self, items: list[str]) -> None:
            for value in items:
                self.addItem(QListWidgetItem(value))

        def addItem(self, item: QListWidgetItem | str) -> None:
            if isinstance(item, str):
                item = QListWidgetItem(item)
            self._items.append(item)

        def clear(self) -> None:
            self._items.clear()

        def item(self, index: int) -> QListWidgetItem:
            return self._items[index]

        def count(self) -> int:
            return len(self._items)

        def setMaximumWidth(self, width: int) -> None:
            self._max_width = width

        def setVisible(self, visible: bool) -> None:
            self._visible = visible

        def setContextMenuPolicy(self, policy: object) -> None:
            self._context_policy = policy

    class QListView(QWidget):
        doubleClicked = qtcore.Signal(object)
        clicked = qtcore.Signal(object)
        customContextMenuRequested = qtcore.Signal(object)

        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._model = None
            self._visible = True
            self._context_policy = None

        def setViewMode(self, _mode: object) -> None:
            pass

        def setIconSize(self, _size: object) -> None:
            pass

        def setResizeMode(self, _mode: object) -> None:
            pass

        def setSpacing(self, _spacing: int) -> None:
            pass

        def setModel(self, model: object) -> None:
            self._model = model

        def model(self) -> object | None:
            return self._model

        def setVisible(self, visible: bool) -> None:
            self._visible = visible

        def setContextMenuPolicy(self, policy: object) -> None:
            self._context_policy = policy

    class QToolBar(QWidget):
        def __init__(self, title: str | None = None, parent: object | None = None) -> None:
            super().__init__(parent)
            self.title = title or ""
            self._movable = True
            self._actions: list[object] = []

        def setMovable(self, movable: bool) -> None:
            self._movable = movable

        def addAction(self, action: object) -> None:
            self._actions.append(action)

        def addWidget(self, widget: object) -> None:
            self._actions.append(widget)

        def addSeparator(self) -> None:
            self._actions.append("separator")
    class QMenu(QWidget):
        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._actions: list[object] = []

        def addAction(self, action: object) -> None:
            self._actions.append(action)

        def addSeparator(self) -> None:
            self._actions.append("separator")

        def exec(self, *_args, **_kwargs) -> None:
            pass

    class QFileDialog:
        @staticmethod
        def getOpenFileNames(*_args, **_kwargs) -> tuple[list[str], str]:
            return [], ""

        @staticmethod
        def getOpenFileName(*_args, **_kwargs) -> tuple[str, str]:
            return "", ""

    class QPushButton(QWidget):
        clicked = qtcore.Signal()

        def __init__(self, text: str = "", parent: object | None = None) -> None:
            super().__init__(parent)
            self._text = text

        def setText(self, text: str) -> None:
            self._text = text

        def setEnabled(self, _enabled: bool) -> None:
            pass

        def click(self) -> None:
            type(self).clicked.__get__(self).emit()

    class QToolButton(QPushButton):
        pass

    class QScrollArea(QWidget):
        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._widget = None
            self._resizable = False

        def setWidgetResizable(self, value: bool) -> None:
            self._resizable = value

        def setWidget(self, widget: object) -> None:
            self._widget = widget

        def widget(self) -> object | None:
            return self._widget

    class QSplitter(QWidget):
        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._widgets: list[object] = []

        def addWidget(self, widget: object) -> None:
            self._widgets.append(widget)

        def setStretchFactor(self, *_args, **_kwargs) -> None:
            pass

    class QLabel(QWidget):
        def __init__(self, text: str = "", parent: object | None = None) -> None:
            super().__init__(parent)
            self._text = text
            self._alignment = Qt.AlignCenter
            self._pixmap = None
            self._word_wrap = False
            self._fixed_height = None

        def setAlignment(self, alignment: int) -> None:
            self._alignment = alignment

        def setPixmap(self, _pixmap: object) -> None:
            self._pixmap = _pixmap

        def resize(self, _size: object) -> None:
            pass

        def setText(self, text: str) -> None:
            self._text = text

        def setWordWrap(self, wrap: bool) -> None:
            self._word_wrap = wrap

        def setFixedHeight(self, height: int) -> None:
            self._fixed_height = height

    class QSlider(QWidget):
        valueChanged = qtcore.Signal()

        def __init__(self, orientation: int, parent: object | None = None) -> None:
            super().__init__(parent)
            self._orientation = orientation
            self._value = 0

        def setMinimum(self, value: int) -> None:
            self._min = value

        def setMaximum(self, value: int) -> None:
            self._max = value

        def setValue(self, value: int) -> None:
            self._value = value
            type(self).valueChanged.__get__(self).emit(value)

        def value(self) -> int:
            return getattr(self, "_value", 0)

        def setRange(self, minimum: int, maximum: int) -> None:
            self._min = minimum
            self._max = maximum

    class QShortcut(QWidget):
        activated = qtcore.Signal()

        def __init__(self, _sequence: object, parent: object | None = None) -> None:
            super().__init__(parent)

    class QComboBox(QWidget):
        currentIndexChanged = qtcore.Signal()

        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._items: list[tuple[str, object]] = []
            self._index = 0

        def addItem(self, label: str, userData: object | None = None) -> None:
            self._items.append((label, userData))

        def addItems(self, labels: list[str]) -> None:
            for label in labels:
                self.addItem(label)

        def clear(self) -> None:
            self._items.clear()
            self._index = 0

        def currentData(self) -> object:
            if 0 <= self._index < len(self._items):
                return self._items[self._index][1]
            return None

        def currentText(self) -> str:
            if 0 <= self._index < len(self._items):
                return self._items[self._index][0]
            return ""

        def setCurrentIndex(self, index: int) -> None:
            self._index = index
            type(self).currentIndexChanged.__get__(self).emit(index)

        def findData(self, data: object) -> int:
            for idx, (_, value) in enumerate(self._items):
                if value == data:
                    return idx
            return -1

        def findText(self, text: str) -> int:
            for idx, (label, _) in enumerate(self._items):
                if label == text:
                    return idx
            return -1

        def blockSignals(self, _block: bool) -> None:
            pass

    class QSpacerItem:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

    class QSizePolicy:
        Expanding = 0
        Minimum = 0

    class QMessageBox:
        @staticmethod
        def warning(*_args, **_kwargs) -> None:
            pass

    class QLineEdit(QWidget):
        textChanged = qtcore.Signal()

        def __init__(self, text: str = "", parent: object | None = None) -> None:
            super().__init__(parent)
            self._text = text
            self._placeholder = ""
            self._readonly = False

        def setText(self, text: str) -> None:
            self._text = text
            type(self).textChanged.__get__(self).emit(text)

        def text(self) -> str:
            return self._text

        def setPlaceholderText(self, placeholder: str) -> None:
            self._placeholder = placeholder

        def setReadOnly(self, readonly: bool) -> None:
            self._readonly = readonly

    class QTextEdit(QWidget):
        def __init__(self, text: str = "", parent: object | None = None) -> None:
            super().__init__(parent)
            self._text = text
            self._readonly = False
            self._placeholder = ""

        def setPlainText(self, text: str) -> None:
            self._text = text

        def toPlainText(self) -> str:
            return self._text

        def setReadOnly(self, readonly: bool) -> None:
            self._readonly = readonly

        def setPlaceholderText(self, placeholder: str) -> None:
            self._placeholder = placeholder

    class QFormLayout:
        def __init__(self, parent: object | None = None) -> None:
            self._rows: list[tuple[str, object]] = []

        def addRow(self, label: str, widget: object) -> None:
            self._rows.append((label, widget))

    class QDockWidget(QWidget):
        NoDockWidgetFeatures = 0

        def __init__(self, title: str = "", parent: object | None = None) -> None:
            super().__init__(parent)
            self.title = title
            self._widget = None
            self._features = self.NoDockWidgetFeatures

        def setFeatures(self, features: int) -> None:
            self._features = features

        def setWidget(self, widget: object) -> None:
            self._widget = widget

        def widget(self) -> object | None:
            return self._widget

    class QSpinBox(QWidget):
        valueChanged = qtcore.Signal()

        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._min = 0
            self._max = 100
            self._value = 0

        def setRange(self, minimum: int, maximum: int) -> None:
            self._min = minimum
            self._max = maximum

        def setValue(self, value: int) -> None:
            self._value = max(self._min, min(self._max, value))
            type(self).valueChanged.__get__(self).emit(self._value)

        def value(self) -> int:
            return self._value

    class QDate:
        def __init__(self, year: int, month: int, day: int) -> None:
            self.year = year
            self.month = month
            self.day = day

        @classmethod
        def currentDate(cls) -> "QDate":
            return cls(2000, 1, 1)

        def toString(self, _format: str) -> str:
            return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"

    class QDateEdit(QWidget):
        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._date = QDate.currentDate()

        def setCalendarPopup(self, _popup: bool) -> None:
            pass

        def setDisplayFormat(self, _fmt: str) -> None:
            pass

        def setDate(self, date: QDate) -> None:
            self._date = date

        def date(self) -> QDate:
            return self._date

    class QTabWidget(QWidget):
        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._tabs: list[tuple[QWidget, str]] = []

        def addTab(self, widget: QWidget, label: str) -> None:
            self._tabs.append((widget, label))

    qtwidgets.QWidget = QWidget
    qtwidgets.QFrame = QFrame
    qtwidgets.QApplication = QApplication
    qtwidgets.QVBoxLayout = QVBoxLayout
    qtwidgets.QHBoxLayout = QHBoxLayout
    qtwidgets.QStackedWidget = QStackedWidget
    qtwidgets.QMainWindow = QMainWindow
    qtwidgets.QHeaderView = QHeaderView
    qtwidgets.QAbstractItemView = QAbstractItemView
    qtwidgets.QTableView = QTableView
    qtwidgets.QListWidget = QListWidget
    qtwidgets.QListWidgetItem = QListWidgetItem
    qtwidgets.QListView = QListView
    qtwidgets.QToolBar = QToolBar
    qtwidgets.QMenu = QMenu
    qtwidgets.QFileDialog = QFileDialog
    qtwidgets.QPushButton = QPushButton
    qtwidgets.QToolButton = QToolButton
    qtwidgets.QScrollArea = QScrollArea
    qtwidgets.QSplitter = QSplitter
    qtwidgets.QLabel = QLabel
    qtwidgets.QSlider = QSlider
    qtwidgets.QShortcut = QShortcut
    qtwidgets.QComboBox = QComboBox
    qtwidgets.QSpacerItem = QSpacerItem
    qtwidgets.QSizePolicy = QSizePolicy
    qtwidgets.QMessageBox = QMessageBox
    qtwidgets.QLineEdit = QLineEdit
    qtwidgets.QTextEdit = QTextEdit
    qtwidgets.QFormLayout = QFormLayout
    qtwidgets.QDockWidget = QDockWidget
    qtwidgets.QSpinBox = QSpinBox
    qtwidgets.QDate = QDate
    qtwidgets.QDateEdit = QDateEdit
    qtwidgets.QTabWidget = QTabWidget
    sys.modules["PySide6.QtWidgets"] = qtwidgets
    pkg.QtWidgets = qtwidgets

    # --- QtGui -------------------------------------------------------------------
    qtgui = types.ModuleType("PySide6.QtGui")

    class QAction(qtcore.QObject):
        triggered = qtcore.Signal()

        def __init__(self, text: str = "", parent: object | None = None) -> None:
            super().__init__(parent)
            self.text = text

    class QKeySequence:
        Open = "Ctrl+O"

    class QImage:
        Format_RGB888 = 0

        def __init__(self, *args, **kwargs) -> None:
            pass

    class QPixmap:
        def __init__(self, *args, **kwargs) -> None:
            self._is_null = False

        @classmethod
        def fromImage(cls, _image: QImage) -> "QPixmap":
            return cls()

        def size(self):  # noqa: D401
            return (1, 1)

        def fill(self, _colour: object) -> None:
            pass

        def isNull(self) -> bool:
            return self._is_null

        def scaled(self, *args, **kwargs) -> "QPixmap":
            return self

        def save(self, *_args, **_kwargs) -> None:
            pass

    class QIcon:
        def __init__(self, path: str | None = None) -> None:
            self.path = path

    class QCursor:
        @staticmethod
        def pos() -> tuple[int, int]:
            return (0, 0)

    class QDragEnterEvent:
        def mimeData(self):  # noqa: N802
            return types.SimpleNamespace(hasUrls=lambda: False, urls=lambda: [])

        def acceptProposedAction(self) -> None:
            pass

        def ignore(self) -> None:
            pass

    class QDropEvent(QDragEnterEvent):
        pass

    qtgui.QAction = QAction
    qtgui.QKeySequence = QKeySequence
    qtgui.QImage = QImage
    qtgui.QPixmap = QPixmap
    qtgui.QIcon = QIcon
    qtgui.QCursor = QCursor
    qtgui.QDragEnterEvent = QDragEnterEvent
    qtgui.QDropEvent = QDropEvent
    sys.modules["PySide6.QtGui"] = qtgui
    pkg.QtGui = qtgui


def _install_fitz_stub() -> None:
    if importlib.util.find_spec("fitz") is not None:
        return

    module = types.ModuleType("fitz")
    module.__STUB__ = True

    class Matrix:
        def __init__(self, x: float = 1.0, y: float = 1.0) -> None:
            self.x = x
            self.y = y

    class Pixmap:
        def __init__(self) -> None:
            self.width = 1
            self.height = 1
            self.stride = 3
            self.samples = b"\x00\x00\x00"

    class Page:
        def __init__(self, document: "Document") -> None:
            self._document = document

        def insert_text(self, _position, _text: str) -> None:
            pass

        def get_pixmap(self, matrix: Matrix | None = None, alpha: bool = False) -> Pixmap:
            return Pixmap()

    class Document:
        def __init__(self, path: str | Path | None = None) -> None:
            self.metadata: dict[str, str] = {}
            self._pages: list[Page] = [Page(self)]
            self._path = Path(path) if path else None

        def new_page(self) -> Page:
            page = Page(self)
            self._pages.append(page)
            return page

        def load_page(self, index: int) -> Page:
            return self._pages[index]

        @property
        def page_count(self) -> int:
            return len(self._pages)

        def save(self, path: str | Path) -> None:
            path = Path(path)
            path.write_bytes(b"%PDF-1.4\n% Stub document\n")
            self._path = path

        def close(self) -> None:
            pass

    def open(path: str | Path | None = None) -> Document:
        return Document(path)

    module.Matrix = Matrix
    module.Pixmap = Pixmap
    module.Page = Page
    module.Document = Document
    module.open = open
    sys.modules["fitz"] = module


_install_pyside6_stub()
_install_fitz_stub()
