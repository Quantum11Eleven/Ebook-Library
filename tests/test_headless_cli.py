from __future__ import annotations

from shelfie import cli_stub


def test_cli_default_runs():
    assert cli_stub.main([]) == 0


def test_cli_lists_books(capsys):
    code = cli_stub.main(["--list"])
    captured = capsys.readouterr()
    assert code == 0
    assert "Your First 1000 Copies" in captured.out


def test_cli_lists_genres(capsys):
    code = cli_stub.main(["--genres"])
    captured = capsys.readouterr()
    assert code == 0
    assert "Spirituality, Consciousness & Metaphysics" in captured.out
