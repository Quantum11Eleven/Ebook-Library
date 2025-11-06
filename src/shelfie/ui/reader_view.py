from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ReaderView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ReaderView")
        top = QHBoxLayout()
        self.btnBack = QPushButton("← Library")
        self.lblTitle = QLabel("(No file)")
        self.btnZoomOut = QPushButton("-")
        self.btnZoomReset = QPushButton("100%")
        self.btnZoomIn = QPushButton("+")
        self.cmbTheme = QComboBox()
        self.cmbTheme.addItems(["Light", "Dark", "Sepia"])
        for widget in (
            self.btnBack,
            self.lblTitle,
            self.btnZoomOut,
            self.btnZoomReset,
            self.btnZoomIn,
            self.cmbTheme,
        ):
            top.addWidget(widget)
        top.addStretch(1)

        splitter = QSplitter()
        tabs = QTabWidget()
        tabs.addTab(QTextEdit("TOC (stub)"), "TOC")
        tabs.addTab(QTextEdit("Notes (stub)"), "Notes")
        self.pdfCanvas = QTextEdit("PDF Canvas Placeholder\n(PyMuPDF integration next)")
        self.pdfCanvas.setReadOnly(True)
        splitter.addWidget(tabs)
        splitter.addWidget(self.pdfCanvas)
        splitter.setStretchFactor(1, 1)

        root = QVBoxLayout(self)
        bar = QWidget()
        bar.setLayout(top)
        root.addWidget(bar)
        root.addWidget(splitter, 1)

    def setTitle(self, title: str) -> None:
        self.lblTitle.setText(title)
