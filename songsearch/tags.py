"""Utilities for reading audio metadata tags.

This module provides :func:`read_tags` which extracts common
metadata fields from audio files using the `mutagen` library.  The
function is tolerant to missing tags and parsing errors and always
returns a dictionary with the expected keys.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple

from mutagen import File as MutagenFile

from .logger import logger


@dataclass
class SongTags:
    """Simple container for metadata fields."""

    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[str] = None
    month: Optional[str] = None
    genre: Optional[str] = None


def _first_value(audio: Dict[str, Any], key: str) -> Optional[str]:
    """Return the first value for *key* in *audio* if present."""
    if key in audio and audio[key]:
        value = audio[key][0]
        return str(value) if value is not None else None
    return None


def _parse_date(value: Any) -> Tuple[Optional[str], Optional[str]]:
    """Extract year and month from *value*.

    The value may be ``None``, a list, or a string in the forms
    ``YYYY`` or ``YYYY-MM``.  Month values are zero padded when
    possible.
    """
    if not value:
        return None, None

    # ``mutagen`` may return the date tag as a list which ``str`` would
    # render like ``['1999-07']``.  Splitting such representation would
    # include the brackets and quotes producing invalid year/month values.
    # Accept sequences and pick the first element before converting to
    # string.  This keeps behaviour consistent with ``_first_value`` which
    # already returns the first entry for tag lists.
    if isinstance(value, (list, tuple)):
        if not value:
            return None, None
        value = value[0]

    date_str = str(value).replace("/", "-")
    parts = date_str.split("-")
    year = parts[0] or None
    month = None
    if len(parts) > 1 and parts[1]:
        month = parts[1].zfill(2)
    return year, month


def read_tags(file_path: str) -> Dict[str, Optional[str]]:
    """Read common audio tags from *file_path*.

    Parameters
    ----------
    file_path:
        Path to the audio file.

    Returns
    -------
    Dict[str, Optional[str]]
        Dictionary with keys ``title``, ``artist``, ``album``, ``year``,
        ``month`` and ``genre``.  Missing tags are represented as
        ``None``.
    """

    tags = SongTags()

    try:
        audio = MutagenFile(file_path, easy=True)
        if not audio:
            return asdict(tags)

        tags.title = _first_value(audio, "title")
        tags.artist = _first_value(audio, "artist")
        tags.album = _first_value(audio, "album")
        tags.genre = _first_value(audio, "genre")

        date_val = (
            _first_value(audio, "date")
            or _first_value(audio, "originaldate")
            or _first_value(audio, "year")
        )
        tags.year, tags.month = _parse_date(date_val)

    except Exception as exc:  # pragma: no cover - defensive
        logger.debug(f"Unable to read tags from {file_path}: {exc}")

    return asdict(tags)
