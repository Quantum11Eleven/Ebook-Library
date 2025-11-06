from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpacerItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class TTSBar(QWidget):
    """Mini player for controlling text-to-speech playback."""

    play_requested = Signal()
    stop_requested = Signal()
    voice_changed = Signal(str)
    speed_changed = Signal(float)
    pitch_changed = Signal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._play_button = QPushButton("Play", self)
        self._play_button.clicked.connect(self.play_requested)

        self._stop_button = QPushButton("Stop", self)
        self._stop_button.clicked.connect(self.stop_requested)
        self._stop_button.setEnabled(False)

        self._voice_selector = QComboBox(self)
        self._voice_selector.currentIndexChanged.connect(self._emit_voice_change)

        self._speed_slider = QSlider(Qt.Horizontal, self)
        self._speed_slider.setRange(50, 200)
        self._speed_slider.setValue(100)
        self._speed_slider.valueChanged.connect(self._emit_speed_change)
        self._speed_label = QLabel("1.0×", self)

        self._pitch_slider = QSlider(Qt.Horizontal, self)
        self._pitch_slider.setRange(80, 120)
        self._pitch_slider.setValue(100)
        self._pitch_slider.valueChanged.connect(self._emit_pitch_change)
        self._pitch_label = QLabel("1.0×", self)

        self._status_label = QLabel("Ready", self)
        self._status_label.setObjectName("ttsStatusLabel")

        line_one = QHBoxLayout()
        line_one.addWidget(self._play_button)
        line_one.addWidget(self._stop_button)
        line_one.addSpacing(12)
        line_one.addWidget(QLabel("Voice", self))
        line_one.addWidget(self._voice_selector, 1)
        line_one.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed", self))
        speed_layout.addWidget(self._speed_slider)
        speed_layout.addWidget(self._speed_label)

        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(QLabel("Pitch", self))
        pitch_layout.addWidget(self._pitch_slider)
        pitch_layout.addWidget(self._pitch_label)

        line_two = QHBoxLayout()
        line_two.addLayout(speed_layout)
        line_two.addSpacing(16)
        line_two.addLayout(pitch_layout)

        layout = QVBoxLayout(self)
        layout.addLayout(line_one)
        layout.addLayout(line_two)
        layout.addWidget(self._status_label)
        self.setLayout(layout)

    # -- control helpers ---------------------------------------------------
    def set_playing(self, playing: bool) -> None:
        self._play_button.setEnabled(not playing)
        self._stop_button.setEnabled(playing)
        if playing:
            self.set_status("Speaking…")
        else:
            self.set_status("Ready")

    def set_status(self, message: str) -> None:
        self._status_label.setText(message)

    def set_voice_options(self, voices: list[tuple[str, str]], selected: str | None) -> None:
        self._voice_selector.blockSignals(True)
        self._voice_selector.clear()
        self._voice_selector.addItem("System default", userData="")
        for voice_id, label in voices:
            self._voice_selector.addItem(label, userData=voice_id)
        if selected:
            index = self._voice_selector.findData(selected)
            if index >= 0:
                self._voice_selector.setCurrentIndex(index)
        else:
            self._voice_selector.setCurrentIndex(0)
        self._voice_selector.blockSignals(False)

    def set_speed_value(self, speed: float) -> None:
        clamped = max(0.5, min(2.0, speed))
        self._speed_slider.blockSignals(True)
        self._speed_slider.setValue(int(clamped * 100))
        self._speed_slider.blockSignals(False)
        self._update_speed_label(clamped)

    def set_pitch_value(self, pitch: float) -> None:
        clamped = max(0.8, min(1.2, pitch))
        self._pitch_slider.blockSignals(True)
        self._pitch_slider.setValue(int(clamped * 100))
        self._pitch_slider.blockSignals(False)
        self._update_pitch_label(clamped)

    # -- Qt signal emitters ------------------------------------------------
    def _emit_voice_change(self) -> None:
        voice_id = self._voice_selector.currentData()
        self.voice_changed.emit(voice_id or "")

    def _emit_speed_change(self, value: int) -> None:
        speed = max(0.5, min(2.0, value / 100.0))
        self._update_speed_label(speed)
        self.speed_changed.emit(speed)

    def _emit_pitch_change(self, value: int) -> None:
        pitch = max(0.8, min(1.2, value / 100.0))
        self._update_pitch_label(pitch)
        self.pitch_changed.emit(pitch)

    def _update_speed_label(self, speed: float) -> None:
        self._speed_label.setText(f"{speed:.1f}×")

    def _update_pitch_label(self, pitch: float) -> None:
        self._pitch_label.setText(f"{pitch:.1f}×")
