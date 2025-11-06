from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QDateEdit,
)

STATUSES = ["Unread", "In Progress", "Finished", "Abandoned"]


def _scaled_cover(pixmap: QPixmap, width: int = 160, height: int = 220) -> QPixmap:
    if pixmap.isNull():
        return pixmap
    return pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class BookDetailsPanel(QWidget):
    editRequested = Signal(dict)
    changeCoverRequested = Signal(dict)
    openRequested = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._book: Optional[dict] = None

        self.lblCover = QLabel()
        self.lblCover.setFixedSize(160, 220)
        self.lblCover.setStyleSheet("border:1px solid #223047; border-radius:6px;")

        self.lblTitle = QLabel("—")
        self.lblAuthor = QLabel("—")
        self.lblGenres = QLabel("—")
        self.lblPublish = QLabel("—")
        self.lblPages = QLabel("—")
        self.lblStatus = QLabel("—")
        self.lblPath = QLabel("—")

        self.txtOverview = QTextEdit()
        self.txtOverview.setReadOnly(True)
        self.txtOverview.setPlaceholderText("No overview yet…")

        form = QFormLayout()
        form.addRow("Title", self.lblTitle)
        form.addRow("Author", self.lblAuthor)
        form.addRow("Genres", self.lblGenres)
        form.addRow("Published", self.lblPublish)
        form.addRow("Pages", self.lblPages)
        form.addRow("Status", self.lblStatus)
        form.addRow("File", self.lblPath)

        btnEdit = QPushButton("Edit")
        btnCover = QPushButton("Change Cover…")
        btnOpen = QPushButton("Open in Reader")

        btn_row = QHBoxLayout()
        btn_row.addWidget(btnEdit)
        btn_row.addWidget(btnCover)
        btn_row.addStretch(1)
        btn_row.addWidget(btnOpen)

        left = QVBoxLayout()
        left.addWidget(self.lblCover, alignment=Qt.AlignTop)
        right = QVBoxLayout()
        right.addLayout(form)
        right.addWidget(QLabel("Overview"))
        right.addWidget(self.txtOverview, 1)
        right.addLayout(btn_row)

        root = QHBoxLayout(self)
        root.addLayout(left)
        root.addLayout(right, 1)

        btnEdit.clicked.connect(lambda: self._book and self.editRequested.emit(self._book))
        btnCover.clicked.connect(lambda: self._book and self.changeCoverRequested.emit(self._book))
        btnOpen.clicked.connect(
            lambda: self._book
            and self.openRequested.emit({"path": self._book.get("path", ""), "id": self._book.get("id")})
        )

    def show_book(self, book: dict) -> None:
        self._book = dict(book)
        cover_path = book.get("cover_path")
        pixmap = QPixmap(cover_path) if cover_path else QPixmap()
        if pixmap.isNull():
            pixmap = QPixmap(160, 220)
            fill = getattr(pixmap, "fill", None)
            colour = getattr(Qt, "darkGray", None)
            if callable(fill) and colour is not None:
                fill(colour)
        else:
            pixmap = _scaled_cover(pixmap)
        scaled = pixmap.scaled(self.lblCover.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lblCover.setPixmap(scaled)
        self.lblTitle.setText(book.get("title", "—"))
        self.lblAuthor.setText(book.get("author", "—"))
        genres = ", ".join(book.get("genres", []) or []) or "—"
        self.lblGenres.setText(genres)
        self.lblPublish.setText(book.get("publish_date", "—"))
        pages = book.get("pages")
        self.lblPages.setText(str(pages) if pages else "—")
        self.lblStatus.setText(book.get("status", "—"))
        self.lblPath.setText(book.get("path", "—"))
        self.txtOverview.setPlainText(book.get("overview", ""))


class BookEditPanel(QWidget):
    saved = Signal(dict)
    canceled = Signal()

    def __init__(self, genres_list: list[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._book: Optional[dict] = None
        self._genres = genres_list

        self.edTitle = QLineEdit()
        self.edAuthor = QLineEdit()
        self.cmbGenrePrimary = QComboBox()
        self.cmbGenrePrimary.addItems(["(None)"] + genres_list)
        self.edGenresExtra = QLineEdit()
        self.datePublish = QDateEdit()
        self.datePublish.setCalendarPopup(True)
        self.datePublish.setDisplayFormat("yyyy-MM-dd")
        self.spPages = QSpinBox()
        self.spPages.setRange(0, 100000)
        self.cmbStatus = QComboBox()
        self.cmbStatus.addItems(STATUSES)
        self.edPath = QLineEdit()
        self.edPath.setReadOnly(True)
        self.btnBrowse = QPushButton("…")
        self.txtOverview = QTextEdit()

        form = QFormLayout()
        form.addRow("Title*", self.edTitle)
        form.addRow("Author", self.edAuthor)
        form.addRow("Primary Genre", self.cmbGenrePrimary)
        form.addRow("Extra Genres (comma)", self.edGenresExtra)
        form.addRow("Publish Date", self.datePublish)
        form.addRow("Pages", self.spPages)
        form.addRow("Status", self.cmbStatus)

        path_row = QHBoxLayout()
        path_row.addWidget(self.edPath, 1)
        path_row.addWidget(self.btnBrowse)
        form.addRow("File", path_row)
        form.addRow("Overview", self.txtOverview)

        btnSave = QPushButton("Save")
        btnCancel = QPushButton("Cancel")
        btn_row = QHBoxLayout()
        btn_row.addWidget(btnSave)
        btn_row.addWidget(btnCancel)
        btn_row.addStretch(1)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addLayout(btn_row)

        self.btnBrowse.clicked.connect(self._choose_file)
        btnSave.clicked.connect(self._save)
        btnCancel.clicked.connect(self.canceled.emit)

    def load_book(self, book: dict) -> None:
        self._book = dict(book)
        self.edTitle.setText(book.get("title", ""))
        self.edAuthor.setText(book.get("author", ""))
        genres = book.get("genres") or []
        primary = genres[0] if genres else None
        index = self.cmbGenrePrimary.findText(primary) if primary else -1
        self.cmbGenrePrimary.setCurrentIndex(index if index >= 0 else 0)
        extras = ",".join(genres[1:]) if len(genres) > 1 else ""
        self.edGenresExtra.setText(extras)
        iso = book.get("publish_date", "")
        if iso:
            try:
                parts = [int(part) for part in iso.split("-")]
                year = parts[0]
                month = parts[1] if len(parts) > 1 else 1
                day = parts[2] if len(parts) > 2 else 1
                self.datePublish.setDate(QDate(year, month, day))
            except Exception:
                self.datePublish.setDate(QDate.currentDate())
        else:
            self.datePublish.setDate(QDate.currentDate())
        self.spPages.setValue(int(book.get("pages") or 0))
        status = book.get("status") or STATUSES[0]
        idx = self.cmbStatus.findText(status)
        self.cmbStatus.setCurrentIndex(idx if idx >= 0 else 0)
        self.edPath.setText(book.get("path", ""))
        self.txtOverview.setPlainText(book.get("overview", ""))

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if path:
            self.edPath.setText(path)

    def _save(self) -> None:
        title = self.edTitle.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing title", "Title is required.")
            return
        primary = self.cmbGenrePrimary.currentText()
        genres: list[str] = []
        if primary and primary != "(None)":
            genres.append(primary)
        extras = [segment.strip() for segment in self.edGenresExtra.text().split(",") if segment.strip()]
        genres.extend(extras)

        updated = dict(self._book or {})
        updated.update(
            {
                "title": title,
                "author": self.edAuthor.text().strip(),
                "genres": genres,
                "publish_date": self.datePublish.date().toString("yyyy-MM-dd"),
                "pages": int(self.spPages.value()) or None,
                "status": self.cmbStatus.currentText(),
                "path": self.edPath.text().strip(),
                "overview": self.txtOverview.toPlainText().strip(),
            }
        )
        self.saved.emit(updated)


def choose_cover_for(book: dict, covers_dir: Path) -> dict:
    covers_dir.mkdir(parents=True, exist_ok=True)
    path, _ = QFileDialog.getOpenFileName(None, "Choose Cover Image", "", "Images (*.png *.jpg *.jpeg)")
    if not path:
        return book
    target = covers_dir / f"{book['id']}.jpg"
    pixmap = QPixmap(path)
    if pixmap.isNull():
        return book
    scaled = pixmap.scaled(600, 900, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    scaled.save(str(target), "JPG", quality=92)
    updated = dict(book)
    updated["cover_path"] = str(target)
    return updated

