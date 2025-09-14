"""Tests for enrich_with_musicbrainz with mocked external services."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import songsearch.musicbrainz as mb


def test_enrich_with_musicbrainz_mock(monkeypatch):
    dummy_fpcalc = "/usr/bin/fpcalc"

    def fake_detect_fpcalc():
        return dummy_fpcalc

    monkeypatch.setattr(mb, "detect_fpcalc", fake_detect_fpcalc)

    class FakeAcoustid:
        @staticmethod
        def fingerprint_file(file_path, fpcalc_path=None):
            assert fpcalc_path == dummy_fpcalc
            return 123, "abc"

        @staticmethod
        def lookup(api_key, fingerprint, duration):
            return {"results": [{"recordings": [{"id": "rec123"}]}]}

    monkeypatch.setattr(mb, "pyacoustid", FakeAcoustid)

    class FakeMB:
        @staticmethod
        def set_useragent(*args, **kwargs):
            pass

        @staticmethod
        def get_recording_by_id(recording_id, includes=None):
            return {
                "recording": {
                    "title": "Test Title",
                    "artist-credit": [{"artist": {"name": "Test Artist"}}],
                    "releases": [{"title": "Test Album", "date": "2015-03-01"}],
                    "genres": [{"name": "Rock"}],
                }
            }

    monkeypatch.setattr(mb, "musicbrainzngs", FakeMB)

    result = mb.enrich_with_musicbrainz("dummy.mp3")
    assert result["title"] == "Test Title"
    assert result["artist"] == "Test Artist"
    assert result["album"] == "Test Album"
    assert result["year"] == "2015"
    assert result["genre"] == "Rock"
