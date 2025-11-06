from __future__ import annotations

from shelfie import bootstrap
from shelfie.main import main as shelfie_main


def test_main_headless_runs_without_pyside6(monkeypatch):
    monkeypatch.setattr(bootstrap, "has_pyside6", lambda: False)
    assert shelfie_main(["--headless"]) == 0
