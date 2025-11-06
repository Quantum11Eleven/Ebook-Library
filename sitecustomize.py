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

    qtcore.Qt = Qt
    qtcore.QObject = QObject
    qtcore.Signal = Signal
    qtcore.QModelIndex = QModelIndex
    qtcore.QAbstractTableModel = QAbstractTableModel
    sys.modules["PySide6.QtCore"] = qtcore
    pkg.QtCore = qtcore

    # --- QtWidgets --------------------------------------------------------------
    qtwidgets = types.ModuleType("PySide6.QtWidgets")

    class QWidget(QObject):
        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._layout = None

        def setAcceptDrops(self, _enabled: bool) -> None:
            pass

        def setLayout(self, layout) -> None:
            self._layout = layout

        def layout(self):
            return self._layout

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

    class QVBoxLayout:
        def __init__(self, parent: object | None = None) -> None:
            self._parent = parent
            self._children: list[object] = []

        def setContentsMargins(self, *args: object) -> None:
            pass

        def addWidget(self, widget: object) -> None:
            self._children.append(widget)

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

    class QListWidget(QWidget):
        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._items: list[str] = []
            self._max_width = None

        def addItems(self, items: list[str]) -> None:
            self._items.extend(items)

        def setMaximumWidth(self, width: int) -> None:
            self._max_width = width

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

    class QFileDialog:
        @staticmethod
        def getOpenFileNames(*_args, **_kwargs) -> tuple[list[str], str]:
            return [], ""

        @staticmethod
        def getOpenFileName(*_args, **_kwargs) -> tuple[str, str]:
            return "", ""

    class QScrollArea(QWidget):
        def __init__(self, parent: object | None = None) -> None:
            super().__init__(parent)
            self._widget = None

        def setWidgetResizable(self, _value: bool) -> None:
            pass

        def setWidget(self, widget: object) -> None:
            self._widget = widget

    class QLabel(QWidget):
        def __init__(self, text: str = "", parent: object | None = None) -> None:
            super().__init__(parent)
            self._text = text
            self._alignment = Qt.AlignCenter

        def setAlignment(self, alignment: int) -> None:
            self._alignment = alignment

        def setPixmap(self, _pixmap: object) -> None:
            pass

        def resize(self, _size: object) -> None:
            pass

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

    class QShortcut(QWidget):
        activated = qtcore.Signal()

        def __init__(self, _sequence: object, parent: object | None = None) -> None:
            super().__init__(parent)

    qtwidgets.QWidget = QWidget
    qtwidgets.QApplication = QApplication
    qtwidgets.QVBoxLayout = QVBoxLayout
    qtwidgets.QStackedWidget = QStackedWidget
    qtwidgets.QMainWindow = QMainWindow
    qtwidgets.QHeaderView = QHeaderView
    qtwidgets.QAbstractItemView = QAbstractItemView
    qtwidgets.QTableView = QTableView
    qtwidgets.QListWidget = QListWidget
    qtwidgets.QToolBar = QToolBar
    qtwidgets.QFileDialog = QFileDialog
    qtwidgets.QScrollArea = QScrollArea
    qtwidgets.QLabel = QLabel
    qtwidgets.QSlider = QSlider
    qtwidgets.QShortcut = QShortcut
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
            pass

        @classmethod
        def fromImage(cls, _image: QImage) -> "QPixmap":
            return cls()

        def size(self):  # noqa: D401
            return (1, 1)

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
