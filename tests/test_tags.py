import types
import os, sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from songsearch import tags as tags_module


class DummyAudio(dict):
    """A minimal mapping mimicking Mutagen's EasyID3 behavior."""
    pass


def test_read_tags_basic(monkeypatch):
    dummy = DummyAudio(
        {
            "title": ["My Song"],
            "artist": ["An Artist"],
            "album": ["An Album"],
            "genre": ["Rock"],
            "date": ["1999-7"],
        }
    )

    def fake_mutagen_file(path, easy=True):
        return dummy

    monkeypatch.setattr(tags_module, "MutagenFile", fake_mutagen_file)
    result = tags_module.read_tags("dummy.mp3")
    assert result["title"] == "My Song"
    assert result["artist"] == "An Artist"
    assert result["year"] == "1999"
    assert result["month"] == "07"
    assert result["genre"] == "Rock"


def test_read_tags_no_audio(monkeypatch):
    def fake_mutagen_file(path, easy=True):
        return None

    monkeypatch.setattr(tags_module, "MutagenFile", fake_mutagen_file)
    result = tags_module.read_tags("missing.mp3")
    assert all(v is None for v in result.values())
