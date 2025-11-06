BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT,
    year INTEGER,
    isbn TEXT,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL UNIQUE,
    pages INTEGER DEFAULT 0,
    added_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS book_assets (
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    cover_path TEXT,
    thumb_path TEXT,
    PRIMARY KEY (book_id)
);

CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS book_genres (
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, genre_id)
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS book_tags (
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, tag_id)
);

CREATE TABLE IF NOT EXISTS reading_state (
    book_id INTEGER PRIMARY KEY REFERENCES books(id) ON DELETE CASCADE,
    last_page INTEGER DEFAULT 0,
    percent REAL DEFAULT 0,
    last_opened_at TEXT,
    total_read_minutes INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS highlights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    page INTEGER NOT NULL,
    rect_json TEXT NOT NULL,
    text TEXT,
    color TEXT,
    note TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tts_prefs (
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    voice_id TEXT,
    speed REAL DEFAULT 1.0,
    pitch REAL DEFAULT 1.0,
    last_position_ms INTEGER DEFAULT 0,
    PRIMARY KEY (book_id)
);

CREATE INDEX IF NOT EXISTS idx_books_title_author ON books(title, author);
CREATE INDEX IF NOT EXISTS idx_book_tags ON book_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_highlights_text ON highlights(text);

COMMIT;
