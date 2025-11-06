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
    def __init__(self, *args, parent=None, **kwargs):
        if args and isinstance(args[0], QWidget):
            parent = args[0]
            args = args[1:]
        super().__init__(parent)
        self.setObjectName("ReaderView")

        top_layout = QHBoxLayout()
        self.btnBack = QPushButton("\u2190 Library")
        self.lblTitle = QLabel("Title • Page 1/1")
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
            top_layout.addWidget(widget)
        top_layout.addStretch(1)

        splitter = QSplitter()
        tabs = QTabWidget()
        tabs.addTab(QTextEdit("TOC (stub)"), "TOC")
        tabs.addTab(QTextEdit("Notes (stub)"), "Notes")

        pdf_canvas = QTextEdit("PDF Canvas Placeholder\n(PyMuPDF integration in next step)")
        pdf_canvas.setReadOnly(True)

        splitter.addWidget(tabs)
        splitter.addWidget(pdf_canvas)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout(self)
        top_bar = QWidget()
        top_bar.setLayout(top_layout)
        layout.addWidget(top_bar)
        layout.addWidget(splitter, 1)
