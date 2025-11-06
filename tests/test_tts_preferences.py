from __future__ import annotations

import sqlite3

from shelfie import database
from shelfie.tts.base import TTSPreferences
from shelfie.tts.preferences import load_preferences, save_preferences


def test_save_and_load_preferences(tmp_path) -> None:
    db_path = tmp_path / "tts.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    database.initialize(conn)

    prefs = TTSPreferences(voice_id="voice", speed=1.2, pitch=0.9, last_position_ms=1200)
    save_preferences(conn, 1, prefs)

    loaded = load_preferences(conn, 1)
    assert loaded == prefs

    default_prefs = load_preferences(conn, 2)
    assert default_prefs == TTSPreferences()
