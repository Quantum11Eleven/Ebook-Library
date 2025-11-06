from __future__ import annotations

import abc
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

ProgressCallback = Callable[[int], None]


@dataclass
class TTSPreferences:
    voice_id: str | None = None
    speed: float = 1.0
    pitch: float = 1.0
    last_position_ms: int = 0


class TTSBackend(abc.ABC):
    name: str

    @abc.abstractmethod
    def speak(self, text: str, *, on_progress: ProgressCallback | None = None) -> None:
        ...

    @abc.abstractmethod
    def stop(self) -> None:
        ...

    @abc.abstractmethod
    def configure(self, *, voice_id: str | None = None, speed: float | None = None, pitch: float | None = None) -> None:
        ...

    def voices(self) -> list[tuple[str, str]]:
        """Return a list of ``(id, name)`` tuples for selectable voices."""

        return []


class BackendFactory(Protocol):
    def __call__(self) -> TTSBackend:
        ...
