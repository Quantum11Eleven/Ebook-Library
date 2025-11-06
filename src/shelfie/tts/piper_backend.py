from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from shelfie.tts.base import ProgressCallback, TTSBackend


class PiperBackend(TTSBackend):
    name = "piper"

    def __init__(self, model_path: Path | None = None, voice_path: Path | None = None) -> None:
        self.model_path = model_path
        self.voice_path = voice_path

    def speak(self, text: str, *, on_progress: ProgressCallback | None = None) -> None:
        if not self.model_path or not self.voice_path:
            raise RuntimeError("Piper backend requires model and voice paths")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            wav_path = Path(tmp_file.name)

        command = [
            "piper",
            "--model",
            str(self.model_path),
            "--output_file",
            str(wav_path),
            "--speaker",
            str(self.voice_path),
        ]

        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert process.stdin is not None
        process.stdin.write(text.encode("utf-8"))
        process.stdin.close()
        process.wait()

        if on_progress:
            on_progress(len(text))

        wav_path.unlink(missing_ok=True)

    def stop(self) -> None:
        # Piper CLI is fire-and-forget; stop requires process management handled by caller.
        return None

    def configure(
        self,
        *,
        voice_id: str | None = None,
        speed: float | None = None,
        pitch: float | None = None,
    ) -> None:
        # Piper settings managed via CLI arguments; expose placeholders for API parity.
        return None
