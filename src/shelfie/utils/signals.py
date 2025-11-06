from PySide6.QtCore import QObject, Signal


class AppSignals(QObject):
    filesDropped = Signal(list)  # list[str]
    showToast = Signal(str)


app_signals = AppSignals()
