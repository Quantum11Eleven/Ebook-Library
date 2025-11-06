from __future__ import annotations

import threading
import pyttsx3

from shelfie.tts.base import ProgressCallback, TTSBackend


class PyttsxBackend(TTSBackend):
    name = "pyttsx3"

    def __init__(self) -> None:
        self._engine = pyttsx3.init()
        self._lock = threading.Lock()

    def speak(self, text: str, *, on_progress: ProgressCallback | None = None) -> None:
        with self._lock:
            self._engine.say(text)
            self._engine.runAndWait()
            if on_progress:
                on_progress(len(text))

    def stop(self) -> None:
        with self._lock:
            self._engine.stop()

    def configure(self, *, voice_id: str | None = None, speed: float | None = None, pitch: float | None = None) -> None:
        with self._lock:
            if voice_id:
                self._engine.setProperty("voice", voice_id)
            if speed:
                self._engine.setProperty("rate", int(200 * speed))
            if pitch:
                self._engine.setProperty("pitch", pitch)
