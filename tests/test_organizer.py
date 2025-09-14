import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from songsearch.organizer import build_destination


def test_build_destination_basic(tmp_path):
    meta = {
        "year": "2023",
        "month": "07",
        "genre": "Rock",
        "artist": "AC/DC",
        "title": "Thunder / Storm",
    }
    dest = build_destination(str(tmp_path), meta, ".MP3")
    expected = (
        tmp_path
        / "2023"
        / "07"
        / "Rock"
        / "AC_DC"
        / "AC_DC - Thunder _ Storm.mp3"
    )
    assert dest == str(expected)


def test_build_destination_defaults(tmp_path):
    dest = build_destination(str(tmp_path), {}, ".FLAC")
    expected = (
        tmp_path
        / "Unknown"
        / "00"
        / "Unknown"
        / "Unknown"
        / "Unknown - Unknown.flac"
    )
    assert dest == str(expected)


def test_safe_truncation_and_ext(tmp_path):
    long = "x" * 100
    meta = {"artist": long, "title": long}
    dest = build_destination(str(tmp_path), meta, ".MP3")
    truncated = "x" * 80
    filename = os.path.basename(dest)
    assert filename == f"{truncated} - {truncated}.mp3"
    artist_dir = os.path.basename(os.path.dirname(dest))
    assert artist_dir == truncated
