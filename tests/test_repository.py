from pathlib import Path

from shelfie.ui.library_view import Book
from shelfie.utils.repository import LibraryRepositoryJson


def test_repository_roundtrip(tmp_path):
    repo_path = tmp_path / "library.json"
    repo = LibraryRepositoryJson(repo_path)
    book = Book(title="Test", author="Author")
    book.path = "/tmp/test.pdf"
    repo.save([book])

    loaded = repo.load()
    assert loaded
    saved = loaded[0]
    assert saved["title"] == "Test"
    assert saved["path"] == "/tmp/test.pdf"


def test_repository_creates_backup(tmp_path):
    repo_path = tmp_path / "library.json"
    repo = LibraryRepositoryJson(repo_path)
    first = Book(title="First", author="One")
    repo.save([first])

    second = Book(title="Second", author="Two")
    repo.save([second])

    backup = repo_path.with_suffix(".bak.json")
    assert backup.exists()
    backup_content = backup.read_text(encoding="utf-8")
    assert "First" in backup_content
