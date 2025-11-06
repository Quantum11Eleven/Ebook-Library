from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import BookLibraryApp as launcher  # noqa: E402


def test_launcher_headless():
    code = launcher.main(["--headless"])
    assert code == 0
