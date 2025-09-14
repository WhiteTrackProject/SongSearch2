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

from .tags import _parse_date


def detect_fpcalc() -> Optional[str]:
    """Return the path to the ``fpcalc`` executable if available.

    The ``pyacoustid`` package relies on the external ``fpcalc`` command
    to generate audio fingerprints.  The command is searched on the
    current ``PATH`` and ``None`` is returned if it cannot be found.
    """
    for path in os.environ.get("PATH", "").split(os.pathsep):
        for name in ("fpcalc", "fpcalc.exe"):
            candidate = os.path.join(path, name)
            if os.path.isfile(candidate):
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
    except Exception:  # pragma: no cover - external tool failure
        # Fingerprinting failed – nothing to enrich with
        return tags

    api_key = os.environ.get("ACOUSTID_API_KEY")

    try:
        lookup = pyacoustid.lookup(api_key, fingerprint, duration)
    except Exception:  # pragma: no cover - network failure
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

    # MusicBrainz requires a user-agent string.  Use a generic one as the
    # project does not provide its own.
    if musicbrainzngs is None:
        return tags
    try:
        musicbrainzngs.set_useragent("songsearch", "0.1")
        mb_data = musicbrainzngs.get_recording_by_id(
            recording_id, includes=["artists", "releases"]
        )
    except Exception:  # pragma: no cover - network failure
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
