from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QComboBox, QHBoxLayout, QPushButton, QSlider, QWidget


class TTSBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ttsBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)

        self.btnPlay = QPushButton("\u25b6")
        self.btnStop = QPushButton("\u25a0")
        self.cmbVoice = QComboBox()
        self.cmbVoice.addItems(["System Default", "Warm Male", "Neutral Female"])

        self.sldSpeed = QSlider(Qt.Horizontal)
        self.sldSpeed.setRange(50, 250)
        self.sldSpeed.setValue(120)

        self.sldPitch = QSlider(Qt.Horizontal)
        self.sldPitch.setRange(-6, 6)
        self.sldPitch.setValue(0)

        self.lblTime = QLabel("00:00")

        layout.addWidget(self.btnPlay)
        layout.addWidget(self.btnStop)
        layout.addWidget(QLabel("Voice"))
        layout.addWidget(self.cmbVoice)
        layout.addWidget(QLabel("Speed"))
        layout.addWidget(self.sldSpeed)
        layout.addWidget(QLabel("Pitch"))
        layout.addWidget(self.sldPitch)
        layout.addStretch(1)
        layout.addWidget(self.lblTime)
