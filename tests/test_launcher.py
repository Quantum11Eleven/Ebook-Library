from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import BookLibraryApp as launcher  # noqa: E402


def test_launcher_headless(monkeypatch):
    # Force shelfie bootstrap to report PySide6 missing and ensure we still
    # succeed when forwarding the --headless flag.
    sys.path.insert(0, str(ROOT / "src"))
    from shelfie import bootstrap  # noqa: E402

    monkeypatch.setattr(bootstrap, "has_pyside6", lambda: False)

    code = launcher.main(["--headless"])
    assert code == 0
