from __future__ import annotations

import importlib.util
import io
import sys

import pytest

from shelfie import bootstrap


def test_has_pyside6_false(monkeypatch):
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)
    assert bootstrap.has_pyside6() is False


def test_has_pyside6_true(monkeypatch):
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())
    assert bootstrap.has_pyside6() is True


def test_missing_message_contains_guidance():
    message = bootstrap.missing_pyside6_message()
    assert "PySide6 is not installed" in message
    assert "pip install" in message


def test_print_missing_and_exit(monkeypatch):
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stderr", buffer)
    with pytest.raises(SystemExit) as exc:
        bootstrap.print_missing_and_exit(3)
    assert exc.value.code == 3
    assert "PySide6 is not installed" in buffer.getvalue()
