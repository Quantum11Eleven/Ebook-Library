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
