from songsearch.ui.organizer_panel import OrganizerPanel


def test_edit_updates_plan_and_destination(monkeypatch, qtbot):
    def fake_plan_moves(paths, base):
        return [
            {
                "original_path": "song.mp3",
                "proposed_path": "/dest/OldGenre/2000.mp3",
                "status": "ok",
                "reason": "planned",
                "title": "Title",
                "artist": "Artist",
                "album": "",
                "year": "2000",
                "month": "",
                "genre": "OldGenre",
            }
        ]

    def fake_build(base, meta, ext):
        return f"{base}/{meta['genre']}/{meta['year']}{ext}"

    monkeypatch.setattr("songsearch.ui.organizer_panel.plan_moves", fake_plan_moves)
    monkeypatch.setattr("songsearch.ui.organizer_panel.build_destination", fake_build)

    panel = OrganizerPanel()
    qtbot.addWidget(panel)
    panel.file_paths = ["song.mp3"]
    panel.dest_dir = "/dest"
    panel.plan_files()

    genre_item = panel.plan_table.item(0, 3)
    genre_item.setText("NewGenre")
    assert panel.plan[0]["genre"] == "NewGenre"
    assert panel.plan[0]["proposed_path"] == "/dest/NewGenre/2000.mp3"

    year_item = panel.plan_table.item(0, 4)
    year_item.setText("2020")
    assert panel.plan[0]["year"] == "2020"
    assert panel.plan[0]["proposed_path"] == "/dest/NewGenre/2020.mp3"

