from __future__ import annotations

import sqlite3

from shelfie.tts.base import TTSPreferences


def load_preferences(conn: sqlite3.Connection, book_id: int) -> TTSPreferences:
    row = conn.execute(
        "SELECT voice_id, speed, pitch, last_position_ms FROM tts_prefs WHERE book_id = ?",
        (book_id,),
    ).fetchone()
    if row is None:
        return TTSPreferences()
    return TTSPreferences(
        voice_id=row["voice_id"],
        speed=row["speed"],
        pitch=row["pitch"],
        last_position_ms=row["last_position_ms"],
    )


def save_preferences(conn: sqlite3.Connection, book_id: int, prefs: TTSPreferences) -> None:
    with conn:
        conn.execute(
            """
            INSERT INTO tts_prefs (book_id, voice_id, speed, pitch, last_position_ms)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(book_id) DO UPDATE SET
                voice_id = excluded.voice_id,
                speed = excluded.speed,
                pitch = excluded.pitch,
                last_position_ms = excluded.last_position_ms
            """,
            (book_id, prefs.voice_id, prefs.speed, prefs.pitch, prefs.last_position_ms),
        )
