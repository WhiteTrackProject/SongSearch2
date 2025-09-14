import csv

from songsearch.organizer import plan_moves, export_plan_csv


def test_plan_moves_success(monkeypatch):
    def fake_read_tags(path):
        assert path == "input/song.MP3"
        return {"title": "Local", "genre": "LocalGenre"}

    def fake_enrich(path):
        assert path == "input/song.MP3"
        return {"title": "MBTitle", "artist": "MBArtist", "year": "2021"}

    def fake_build(base, meta, ext):
        assert base == "/base"
        assert ext == ".MP3"
        assert meta["title"] == "MBTitle"
        assert meta["artist"] == "MBArtist"
        # local genre preserved
        assert meta["genre"] == "LocalGenre"
        return "/final/MBArtist - MBTitle.mp3"

    monkeypatch.setattr("songsearch.organizer.plan.read_tags", fake_read_tags)
    monkeypatch.setattr(
        "songsearch.organizer.plan.enrich_with_musicbrainz", fake_enrich
    )
    monkeypatch.setattr("songsearch.organizer.plan.build_destination", fake_build)

    plan = plan_moves(["input/song.MP3"], "/base")
    assert plan == [
        {
            "original_path": "input/song.MP3",
            "proposed_path": "/final/MBArtist - MBTitle.mp3",
            "status": "ok",
            "reason": "planned",
            "title": "MBTitle",
            "artist": "MBArtist",
            "album": "",
            "year": "2021",
            "month": "",
            "genre": "LocalGenre",
        }
    ]


def test_plan_moves_error(monkeypatch):
    def fake_read_tags(path):
        raise RuntimeError("boom")

    monkeypatch.setattr("songsearch.organizer.plan.read_tags", fake_read_tags)

    plan = plan_moves(["bad.mp3"], "/base")
    assert plan == [
        {
            "original_path": "bad.mp3",
            "proposed_path": "",
            "status": "error",
            "reason": "boom",
            "title": "",
            "artist": "",
            "album": "",
            "year": "",
            "month": "",
            "genre": "",
        }
    ]


def test_export_plan_csv(tmp_path):
    plan = [
        {
            "original_path": "a",
            "proposed_path": "b",
            "status": "ok",
            "reason": "planned",
            "title": "t",
            "artist": "ar",
            "album": "al",
            "year": "1",
            "month": "2",
            "genre": "g",
        },
        {
            "original_path": "c",
            "proposed_path": "",
            "status": "error",
            "reason": "oops",
            "title": "",
            "artist": "",
            "album": "",
            "year": "",
            "month": "",
            "genre": "",
        },
    ]

    csv_path = tmp_path / "sub" / "plan.csv"
    ok, errors = export_plan_csv(plan, str(csv_path))
    assert ok == 1
    assert errors == 1
    assert csv_path.exists()

    with open(csv_path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 2
    assert rows[0]["original_path"] == "a"
    assert rows[1]["status"] == "error"
