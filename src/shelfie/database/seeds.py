from __future__ import annotations

import sqlite3

DEFAULT_GENRES = [
    "🚀 Sci-Fi Explorations",
    "🐉 Epic Fantasy",
    "🕵️‍♀️ Mystery & Thrillers",
    "📘 Non-Fiction Insights",
    "🌱 Self-Improvement",
    "🖥️ Technology & Programming",
    "🏛️ Literary Classics",
    "🎨 Graphic Novels & Comics",
    "🧠 Philosophy & Thought",
    "✒️ Poetry & Essays",
]


def seed_default_genres(conn: sqlite3.Connection) -> None:
    existing = {
        row["name"]
        for row in conn.execute("SELECT name FROM genres")
    }
    to_insert = [name for name in DEFAULT_GENRES if name not in existing]
    if not to_insert:
        return
    with conn:
        conn.executemany(
            "INSERT INTO genres (name) VALUES (?)",
            ((name,) for name in to_insert),
        )
