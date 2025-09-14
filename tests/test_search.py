import os
import sys
import pytest

# Ensure the package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from songsearch.db import DatabaseManager
from songsearch.search import fuzzy_search


@pytest.fixture
def sample_db(tmp_path):
    db = DatabaseManager(str(tmp_path / "songs.db"))
    songs = [
        {
            "name": "song1.mp3",
            "artist": "The Beatles",
            "title": "Hey Jude",
            "path": "song1.mp3",
        },
        {
            "name": "song2.mp3",
            "artist": "The Rolling Stones",
            "title": "Paint It Black",
            "path": "song2.mp3",
        },
        {
            "name": "song3.mp3",
            "artist": "Queen",
            "title": "Bohemian Rhapsody",
            "path": "song3.mp3",
        },
    ]
    for song in songs:
        db.add_song(**song)
    return db


def test_fuzzy_search_artist(sample_db):
    results = fuzzy_search(sample_db, "beatles", "artist", 80)
    assert len(results) == 1
    assert results[0]["artist"] == "The Beatles"

    high_threshold = fuzzy_search(sample_db, "beatles", "artist", 85)
    assert high_threshold == []


def test_fuzzy_search_song(sample_db):
    results = fuzzy_search(sample_db, "bohemian", "song", 70)
    assert len(results) == 1
    assert results[0]["title"] == "Bohemian Rhapsody"

    high_threshold = fuzzy_search(sample_db, "bohemian", "song", 80)
    assert high_threshold == []
