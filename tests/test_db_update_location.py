import os
import sys
import pytest

# Ensure the package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from songsearch.db import DatabaseManager


@pytest.fixture
def sample_db(tmp_path):
    db = DatabaseManager(str(tmp_path / "songs.db"))
    db.add_song(name="track1.mp3", artist="Artist", title="Track 1", path="old")
    return db


def test_update_song_location_by_id(sample_db):
    row = sample_db.search_song_like("", "song")[0]
    song_id = row[0]
    sample_db.update_song_location(song_id, "new_path")
    updated = sample_db.search_song_like("", "song")[0]
    assert updated[3] == "new_path"


def test_update_song_location_by_name(sample_db):
    sample_db.update_song_location("track1.mp3", "final_path")
    updated = sample_db.search_song_like("", "song")[0]
    assert updated[3] == "final_path"
