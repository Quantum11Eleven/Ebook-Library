from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsDialog")
        self.setWindowTitle("Settings")

        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        general = QWidget()
        general_form = QFormLayout(general)
        general_form.addRow("Theme", QComboBox())
        general_form.addRow("Library Folder", QLineEdit("%USERPROFILE%/Shelfie"))

        tts = QWidget()
        tts_form = QFormLayout(tts)
        tts_form.addRow("Default Engine", QComboBox())
        tts_form.addRow("Remember speed/pitch", QCheckBox())

        tabs.addTab(general, "General")
        tabs.addTab(tts, "TTS")

        layout.addWidget(tabs)
