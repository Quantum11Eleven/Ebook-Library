from __future__ import annotations

import logging
from typing import Dict

from PySide6.QtCore import QObject, QThread, Signal, Slot

from shelfie.tts import preferences
from shelfie.tts.base import BackendFactory, TTSBackend, TTSPreferences

LOGGER = logging.getLogger(__name__)


class _SpeechWorker(QObject):
    finished = Signal()
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, backend: TTSBackend, text: str) -> None:
        super().__init__()
        self._backend = backend
        self._text = text

    @Slot()
    def run(self) -> None:
        try:
            self._backend.speak(self._text, on_progress=self.progress.emit)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("TTS backend failed")
            self.error.emit(str(exc))
        else:
            self.finished.emit()

    @Slot()
    def stop(self) -> None:
        try:
            self._backend.stop()
        except Exception:  # noqa: BLE001
            LOGGER.debug("TTS backend stop failed", exc_info=True)


class TTSService(QObject):
    """Manage TTS playback and persist preferences per book."""

    started = Signal()
    finished = Signal()
    error = Signal(str)
    progress = Signal(int)
    voices_changed = Signal(list)

    def __init__(
        self,
        conn,
        backends: Dict[str, BackendFactory],
    ) -> None:
        super().__init__()
        self._conn = conn
        self._factories = backends
        self._backend_name = next(iter(backends)) if backends else None
        self._backend: TTSBackend | None = None
        self._thread: QThread | None = None
        self._worker: _SpeechWorker | None = None
        self._book_id: int | None = None
        self._preferences = TTSPreferences()
        if self._backend_name:
            self._backend = self._factories[self._backend_name]()
            self.voices_changed.emit(self.available_voices())

    # -- configuration -----------------------------------------------------
    def available_backends(self) -> list[str]:
        return list(self._factories.keys())

    def available_voices(self) -> list[tuple[str, str]]:
        if not self._backend:
            return []
        try:
            return self._backend.voices()
        except Exception:  # noqa: BLE001
            LOGGER.debug("Voice enumeration failed", exc_info=True)
            return []

    def load_book(self, book_id: int) -> None:
        self._book_id = book_id
        self._preferences = preferences.load_preferences(self._conn, book_id)
        self._apply_preferences()

    def current_preferences(self) -> TTSPreferences:
        return self._preferences

    def set_voice(self, voice_id: str | None) -> None:
        self._preferences.voice_id = voice_id
        self._apply_preferences()
        self._persist_preferences()

    def set_speed(self, speed: float) -> None:
        self._preferences.speed = speed
        self._apply_preferences()
        self._persist_preferences()

    def set_pitch(self, pitch: float) -> None:
        self._preferences.pitch = pitch
        self._apply_preferences()
        self._persist_preferences()

    def _apply_preferences(self) -> None:
        if not self._backend:
            return
        try:
            self._backend.configure(
                voice_id=self._preferences.voice_id,
                speed=self._preferences.speed,
                pitch=self._preferences.pitch,
            )
        except Exception:  # noqa: BLE001
            LOGGER.debug("Applying TTS preferences failed", exc_info=True)

    def _persist_preferences(self) -> None:
        if self._book_id is None:
            return
        preferences.save_preferences(self._conn, self._book_id, self._preferences)

    # -- playback ----------------------------------------------------------
    def speak(self, text: str) -> None:
        if not text.strip():
            self.error.emit("Nothing to read")
            return
        if not self._backend:
            self.error.emit("No TTS backend available")
            return
        self.stop()
        self._worker = _SpeechWorker(self._backend, text)
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.progress.connect(self.progress.emit)
        self._thread.start()
        self.started.emit()

    def stop(self) -> None:
        if self._worker:
            self._worker.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        self._cleanup_thread()

    def _cleanup_thread(self) -> None:
        if self._worker:
            self._worker.deleteLater()
        if self._thread:
            self._thread.deleteLater()
        self._worker = None
        self._thread = None

    @Slot()
    def _on_worker_finished(self) -> None:
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        self._cleanup_thread()
        self.finished.emit()
        self._persist_preferences()

    @Slot(str)
    def _on_worker_error(self, message: str) -> None:
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        self._cleanup_thread()
        self.error.emit(message)

