import os
import re
from typing import Dict

from ..config import DEFAULT_DEST_TEMPLATE


def _safe(s: str, max_len: int = 80) -> str:
    s = (s or "Unknown").strip()
    s = re.sub(r'[\\/:*?"<>|]+', "_", s)
    return s[:max_len]


def build_destination(
    base_dir: str, meta: Dict[str, str], ext: str, template: str = DEFAULT_DEST_TEMPLATE
) -> str:
    values = {
        "year": _safe(meta.get("year") or "Unknown"),
        "month": _safe(meta.get("month") or "00"),
        "genre": _safe(meta.get("genre") or "Unknown"),
        "artist": _safe(meta.get("artist") or "Unknown"),
        "title": _safe(meta.get("title") or "Unknown"),
        "ext": ext.lower(),
    }
    rel = template.format(**values)
    return os.path.normpath(os.path.join(base_dir, rel))
