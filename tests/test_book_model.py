from shelfie.ui.library_view import Book


def test_book_as_dict_contains_expected_fields() -> None:
    book = Book(title="Test Book", author="Author Example", genres=["Science"], path="/tmp/example.pdf")
    data = book.as_dict()
    assert data["title"] == "Test Book"
    assert data["author"] == "Author Example"
    assert data["genres"] == ["Science"]
    assert data["status"] == "Unread"
    assert data["path"] == "/tmp/example.pdf"
    assert "id" in data


def test_book_from_dict_recreates_instance() -> None:
    payload = {
        "id": "abc123",
        "title": "Loaded",
        "author": "Loaded Author",
        "genres": ["Miscellaneous", "Bonus"],
        "publish_date": "2023-05",
        "pages": "320",
        "status": "In Progress",
        "path": "/tmp/loaded.pdf",
        "overview": "Overview text",
    }
    book = Book.from_dict(payload)
    assert book.id == "abc123"
    assert book.title == "Loaded"
    assert book.author == "Loaded Author"
    assert book.genres[0] == "Miscellaneous"
    assert book.pages == 320
    assert book.status == "In Progress"
    assert book.path == "/tmp/loaded.pdf"
