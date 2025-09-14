import os
import sys
import tempfile

# Ensure the package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from songsearch.db import DatabaseManager


def test_search_song_like_song_and_artist():
    """Database searches return matching rows for song titles and artist names."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "songs.db")
        db = DatabaseManager(db_path)
        db.add_song(name="file.mp3", artist="Test Artist", title="Test Song", path="file.mp3")

        # Search by song title
        rows_song = db.search_song_like("Test", mode="song")
        assert len(rows_song) == 1
        assert rows_song[0][4] == "Test Song"

        # Search by artist name
        rows_artist = db.search_song_like("Artist", mode="artist")
        assert len(rows_artist) == 1
        assert rows_artist[0][2] == "Test Artist"
