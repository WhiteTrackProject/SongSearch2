import os
import csv
from typing import List, Dict, Tuple

from songsearch.tags import read_tags
from songsearch.musicbrainz import enrich_with_musicbrainz
from songsearch.organizer.destination import build_destination
from songsearch.logger import logger


def plan_moves(file_paths: List[str], base_dest_dir: str) -> List[Dict[str, str]]:
    """Create a move plan for *file_paths*.

    Each file is inspected using :func:`read_tags` and enriched with
    information from MusicBrainz via :func:`enrich_with_musicbrainz`.
    The resulting metadata is fed into :func:`build_destination` to obtain
    the proposed destination path. Any exceptions are captured and
    reported in the returned plan instead of bubbling up.
    """

    plan: List[Dict[str, str]] = []
    for src in file_paths:
        try:
            ext = os.path.splitext(src)[1]
            local = read_tags(src)
            mb = enrich_with_musicbrainz(src)
            meta = {**local, **mb}
            dest = build_destination(base_dest_dir, meta, ext)
            plan.append(
                {
                    "original_path": src,
                    "proposed_path": dest,
                    "status": "ok",
                    "reason": "planned",
                    "title": meta.get("title") or "",
                    "artist": meta.get("artist") or "",
                    "album": meta.get("album") or "",
                    "year": meta.get("year") or "",
                    "month": meta.get("month") or "",
                    "genre": meta.get("genre") or "",
                }
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Error planning move for %s", src)
            plan.append(
                {
                    "original_path": src,
                    "proposed_path": "",
                    "status": "error",
                    "reason": str(exc),
                    "title": "",
                    "artist": "",
                    "album": "",
                    "year": "",
                    "month": "",
                    "genre": "",
                }
            )
    return plan


def export_plan_csv(plan: List[Dict[str, str]], csv_path: str) -> Tuple[int, int]:
    """Write *plan* to ``csv_path`` and return counts of successes/errors."""

    ok = sum(1 for r in plan if r.get("status") == "ok")
    errors = sum(1 for r in plan if r.get("status") != "ok")

    fields = [
        "original_path",
        "proposed_path",
        "status",
        "reason",
        "title",
        "artist",
        "album",
        "year",
        "month",
        "genre",
    ]

    dir_name = os.path.dirname(csv_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in plan:
            writer.writerow(row)

    return ok, errors
