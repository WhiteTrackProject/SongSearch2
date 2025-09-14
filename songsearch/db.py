import sqlite3
from typing import List, Tuple, Optional, Dict, Any
from .config import DB_PATH
from .logger import logger

SCHEMA = """
CREATE TABLE IF NOT EXISTS songs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  artist TEXT,
  title TEXT,
  album TEXT,
  year TEXT,
  month TEXT,
  genre TEXT,
  path TEXT UNIQUE,
  duration INTEGER,
  file_format TEXT,
  size INTEGER,
  modified_date TEXT,
  mb_recording_id TEXT,
  acoustid TEXT,
  original_path TEXT,
  proposed_path TEXT,
  final_path TEXT,
  move_status TEXT,
  inserted_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_songs_name ON songs(name);
CREATE INDEX IF NOT EXISTS idx_songs_artist ON songs(artist);
CREATE INDEX IF NOT EXISTS idx_songs_title ON songs(title);
"""


class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._conn() as c:
            c.executescript(SCHEMA)

    def clear_database(self):
        with self._conn() as c:
            c.execute("DELETE FROM songs")

    def add_song(self, **kw):
        fields = ",".join(kw.keys())
        placeholders = ",".join(["?"] * len(kw))
        values = list(kw.values())
        try:
            with self._conn() as c:
                c.execute(f"INSERT OR IGNORE INTO songs ({fields}) VALUES ({placeholders})", values)
        except Exception as e:
            logger.error(f"DB add_song error: {e}")

    def update_song_location(self, name: str, new_path: str):
        with self._conn() as c:
            c.execute("UPDATE songs SET path=? WHERE name=?", (new_path, name,))

    def search_song_like(self, query: str, mode: str = "song") -> List[Tuple]:
        col = "title" if mode == "song" else "artist"
        with self._conn() as c:
            return c.execute(f"SELECT id,name,artist,path,title FROM songs WHERE {col} LIKE ?", (f"%{query}%",)).fetchall()

    def fetch_all_for_fuzzy(self) -> List[Tuple]:
        with self._conn() as c:
            return c.execute("SELECT id,name,artist,title,path FROM songs").fetchall()
