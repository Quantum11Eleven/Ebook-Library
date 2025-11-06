from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class ProgressSignal(QObject):
    """Qt signal bridge for background tasks."""

    progressed = Signal(int, str)
    completed = Signal()
    failed = Signal(str)
