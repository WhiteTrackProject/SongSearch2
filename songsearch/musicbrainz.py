import os
from typing import Dict, Any, Optional

try:  # pragma: no cover - optional dependency
    import pyacoustid  # type: ignore
except Exception:  # pragma: no cover - import failure
    pyacoustid = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import musicbrainzngs  # type: ignore
except Exception:  # pragma: no cover - import failure
    musicbrainzngs = None  # type: ignore

from .config import MB_APP_NAME, MB_APP_VERSION, MB_CONTACT, ACOUSTID_API_KEY
from .tags import _parse_date
from .logger import logger


def detect_fpcalc() -> Optional[str]:
    """Return the path to the ``fpcalc`` executable if available.

    The ``pyacoustid`` package relies on the external ``fpcalc`` command
    to generate audio fingerprints.  The command is searched on the
    current ``PATH`` and ``None`` is returned if it cannot be found.
    """
    for path in os.environ.get("PATH", "").split(os.pathsep):
        for name in ("fpcalc", "fpcalc.exe"):
            candidate = os.path.join(path, name)
            # ``fpcalc`` may exist on ``PATH`` but lack execute permissions
            # (e.g. created as a placeholder file in tests or by packaging
            # mistakes).  Returning such a path would later cause confusing
            # failures when trying to run the command.  Guard against this by
            # ensuring the candidate is both a regular file **and**
            # executable for the current user.
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
    return None


def enrich_with_musicbrainz(file_path: str) -> Dict[str, Any]:
    """Fingerprint *file_path* and retrieve metadata from MusicBrainz.

    The function uses ``pyacoustid`` to compute the AcoustID fingerprint of
    the file and then queries the MusicBrainz web service for metadata about
    the best matching recording.  A mapping compatible with
    :class:`~songsearch.tags.SongTags` is returned.  Missing data are omitted
    from the result.
    """
    tags: Dict[str, Any] = {}

    if pyacoustid is None:
        return tags
    try:
        fpcalc_path = detect_fpcalc()
        if fpcalc_path:
            duration, fingerprint = pyacoustid.fingerprint_file(
                file_path, fpcalc_path=fpcalc_path
            )
        else:
            duration, fingerprint = pyacoustid.fingerprint_file(file_path)
    except Exception as exc:  # pragma: no cover - external tool failure
        # Fingerprinting failed – nothing to enrich with
        logger.warning("Fingerprinting failed for %s: %s", file_path, exc)
        return tags

    api_key = ACOUSTID_API_KEY or None
    if not api_key:
        logger.info(
            "ACOUSTID_API_KEY not set; performing lookup without API key which may impose limitations"
        )

    try:
        lookup = pyacoustid.lookup(api_key, fingerprint, duration)
    except Exception as exc:  # pragma: no cover - network failure
        logger.warning("AcoustID lookup failed for %s: %s", file_path, exc)
        return tags

    results = lookup.get("results", []) if isinstance(lookup, dict) else []
    if not results:
        return tags

    # pick the first recording with a MusicBrainz ID
    recording_id: Optional[str] = None
    for entry in results:
        recs = entry.get("recordings") or []
        if recs:
            recording_id = recs[0].get("id")
            break

    if not recording_id:
        return tags

    # MusicBrainz requires a user-agent string.  Configure it using the values
    # from :mod:`songsearch.config` to allow courteous identification.
    if musicbrainzngs is None:
        return tags
    try:
        musicbrainzngs.set_useragent(
            MB_APP_NAME or "songsearch",
            MB_APP_VERSION or "0.1",
            MB_CONTACT or None,
        )
        mb_data = musicbrainzngs.get_recording_by_id(
            recording_id, includes=["artists", "releases"]
        )
    except Exception as exc:  # pragma: no cover - network failure
        logger.warning(
            "MusicBrainz lookup failed for %s (recording %s): %s",
            file_path,
            recording_id,
            exc,
        )
        return tags

    recording = mb_data.get("recording", {}) if isinstance(mb_data, dict) else {}
    if not recording:
        return tags

    title = recording.get("title")
    if title:
        tags["title"] = title

    artists = recording.get("artist-credit")
    if artists:
        artist = artists[0]
        if isinstance(artist, dict):
            tags["artist"] = artist.get("artist", {}).get("name")

    releases = recording.get("releases")
    if releases:
        release = releases[0]
        album = release.get("title")
        if album:
            tags["album"] = album

        year, month = _parse_date(release.get("date"))
        if year:
            tags["year"] = year
        if month:
            tags["month"] = month

    return tags
