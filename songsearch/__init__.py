"""SongSearch package."""

from .tags import read_tags
from .musicbrainz import detect_fpcalc, enrich_with_musicbrainz

__all__ = ["read_tags", "detect_fpcalc", "enrich_with_musicbrainz"]
