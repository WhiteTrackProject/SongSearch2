from typing import List, Dict, Any
from rapidfuzz import process, fuzz
from ..logger import logger
from ..db import DatabaseManager


def fuzzy_search(db: DatabaseManager, query: str, mode: str, threshold: int) -> List[Dict[str, Any]]:
    """Return fuzzy-matched songs from the database.

    Args:
        db: Database manager instance.
        query: Text to search for.
        mode: "artist" to match against artist names, otherwise match song titles/names.
        threshold: Minimum score (0-100) required for a match.
    """
    rows = db.fetch_all_for_fuzzy(query, mode)

    if mode == "artist":
        choices = [(r[2] or "", r) for r in rows]  # artist, row
    else:
        # song mode: use title if available; otherwise fallback to filename without extension
        choices = [((r[3] or r[1] or ""), r) for r in rows]  # title/name, row

    results: List[Dict[str, Any]] = []
    # process.extract returns list of (match_string, score, index); build results manually
    matches = process.extract(
        query,
        [c[0] for c in choices],
        scorer=fuzz.WRatio,
        score_cutoff=threshold,
        limit=50,
    )
    for _match_text, score, idx in matches:
        row = choices[idx][1]
        results.append(
            {
                "id": row[0],
                "name": row[1],
                "artist": row[2],
                "title": row[3],
                "path": row[4],
                "score": score,
            }
        )

    logger.debug("Fuzzy matches for '%s': %d", query, len(results))
    return results
