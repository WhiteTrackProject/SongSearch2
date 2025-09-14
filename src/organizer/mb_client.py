import os
from typing import Dict, Any, Optional, Tuple, List
from .scanner import read_tags  # por si queremos fusionar tags locales como fallback
from ..config import MB_APP_NAME, MB_APP_VERSION, MB_CONTACT, ACOUSTID_API_KEY
from ..logger import logger

# Dependencias externas
# pyacoustid usa Chromaprint (fpcalc) para la huella
try:
    import acoustid
except Exception:
    acoustid = None

try:
    import musicbrainzngs
except Exception:
    musicbrainzngs = None


def detect_fpcalc() -> Optional[str]:
    """Devuelve la ruta a fpcalc si existe en PATH; si no, None."""
    for p in os.environ.get("PATH", "").split(os.pathsep):
        for name in ("fpcalc", "fpcalc.exe"):
            cand = os.path.join(p, name)
            if os.path.isfile(cand):
                return cand
    return None


def _setup_mb():
    """Configura el cliente de MusicBrainz si está disponible."""
    if not musicbrainzngs:
        return False
    try:
        # User-Agent claro y educado: recomendado por MusicBrainz
        musicbrainzngs.set_useragent(MB_APP_NAME or "SongSearch",
                                     MB_APP_VERSION or "1.0",
                                     MB_CONTACT or None)
        # Manejo de rate-limit (1 req/seg aprox). NGS hace gestión básica; evitamos spam.
        return True
    except Exception as e:
        logger.error(f"MusicBrainz init error: {e}")
        return False


def _best_acoustid_result(results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Elige el mejor resultado (score más alto con recordings presentes)."""
    if not results:
        return None
    # Filtramos los que tengan recordings
    valid = [r for r in results if r.get("recordings")]
    if not valid:
        return None
    # Ordenamos por score desc
    valid.sort(key=lambda r: float(r.get("score", 0)), reverse=True)
    return valid[0]


def _extract_basic_from_recording(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Saca título, artista(s) y release-group si existen desde el objeto 'recording' de AcoustID."""
    out = {"title": None, "artist": None, "album": None, "mb_recording_id": None}
    try:
        out["mb_recording_id"] = rec.get("id")
        out["title"] = rec.get("title")

        # Artistas: lista
        artists = []
        for a in rec.get("artists", []) or []:
            if isinstance(a, dict):
                n = a.get("name")
                if n:
                    artists.append(n)
        if not artists and rec.get("artist"):
            artists.append(rec.get("artist"))
        out["artist"] = ", ".join(artists) if artists else None

        # Álbum: mirar releasegroups si vienen en recording (a veces vienen arriba en el nivel de result)
        # En el payload de acoustid.lookup con meta=['recordings','releasegroups'] suelen venir en el nivel superior del result,
        # pero algunas bindings lo injertan también en recording; cubrimos ambos casos en 'enrich_with_musicbrainz'.
    except Exception:
        pass
    return out


def _normalize_date(date_str: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Convierte 'YYYY-MM-DD' o 'YYYY-MM' o 'YYYY' a (year, month) -> ('YYYY', 'MM' or '00')
    """
    if not date_str:
        return None, None
    parts = str(date_str).split("-")
    year = parts[0] if parts and parts[0] else None
    month = parts[1] if len(parts) > 1 and parts[1] else None
    return year, month


def _get_genre_from_mb_recording(recording_id: str) -> Optional[str]:
    """Consulta MusicBrainz para obtener géneros/tags del recording (o release-group) y devuelve el más relevante."""
    if not musicbrainzngs:
        return None
    try:
        # Pide géneros y tags; incluye también releases para, si hace falta, mirar el release-group.
        rec = musicbrainzngs.get_recording_by_id(recording_id,
                                                 includes=["genres", "tags", "releases", "artists", "release-groups"])
        data = rec.get("recording", {})
        # MusicBrainz modernos usan 'genres' (lista de dicts {'name', 'count'})
        genres = data.get("genres", []) or []
        if genres:
            # Ordena por count desc y devuelve el nombre
            genres.sort(key=lambda g: int(g.get("count", 0)), reverse=True)
            return genres[0].get("name")

        # Fallback: tags como género aproximado
        tags = data.get("tags", []) or []
        if tags:
            tags.sort(key=lambda t: int(t.get("count", 0)), reverse=True)
            return tags[0].get("name")

        # Segundo fallback: mirar release-group (si existe)
        rgs = data.get("release-group") or data.get("release-groups") or []
        rg_id = None
        if isinstance(rgs, dict):
            rg_id = rgs.get("id")
        elif isinstance(rgs, list) and rgs:
            rg_id = rgs[0].get("id")

        if rg_id:
            rg = musicbrainzngs.get_release_group_by_id(rg_id, includes=["genres", "tags"])
            g2 = rg.get("release-group", {}).get("genres", []) or []
            if g2:
                g2.sort(key=lambda g: int(g.get("count", 0)), reverse=True)
                return g2[0].get("name")
            t2 = rg.get("release-group", {}).get("tags", []) or []
            if t2:
                t2.sort(key=lambda t: int(t.get("count", 0)), reverse=True)
                return t2[0].get("name")
    except Exception as e:
        logger.debug(f"MB genre fetch error for recording {recording_id}: {e}")
    return None


def enrich_with_musicbrainz(file_path: str) -> Dict[str, Any]:
    """
    Intenta enriquecer metadatos usando AcoustID (+ fpcalc) y MusicBrainz.
    Devuelve dict con posibles claves: title, artist, album, year, month, genre, mb_recording_id, acoustid.
    Política de seguridad:
    - Si falta fpcalc, pyacoustid o la API key -> {} (no rompe nada).
    - Si falla la red o no hay match válido -> {}.
    """
    # Chequeos de entorno
    if not acoustid:
        logger.debug("pyacoustid no disponible; saltando enriquecimiento.")
        return {}
    if not detect_fpcalc():
        logger.debug("fpcalc no detectado; saltando enriquecimiento.")
        return {}
    api_key = (ACOUSTID_API_KEY or "").strip()
    if not api_key:
        logger.debug("ACOUSTID_API_KEY vacío; saltando enriquecimiento.")
        return {}

    # Configurar MusicBrainz client
    use_mb = _setup_mb()

    try:
        # 1) Fingerprint (devuelve duration, fingerprint)
        duration, fp = acoustid.fingerprint_file(file_path)
        # 2) Lookup en AcoustID con metadatos de recordings y releasegroups
        # Documentación: acoustid.lookup(client_key, fingerprint, duration, meta=[...])
        resp = acoustid.lookup(api_key, fp, duration, meta=["recordings", "releasegroups", "compress"])
        results = resp.get("results", []) if isinstance(resp, dict) else []

        best = _best_acoustid_result(results)
        if not best:
            return {}

        out: Dict[str, Any] = {}
        out["acoustid"] = best.get("id")

        # Extraer del recording
        recs = best.get("recordings") or []
        if recs:
            base = _extract_basic_from_recording(recs[0])
            out.update(base)

        # Album y fecha desde releasegroups (en nivel de result)
        rgs = best.get("releasegroups") or []
        if rgs:
            rg = rgs[0]
            # Álbum / título del release-group
            out["album"] = rg.get("title") or out.get("album")
            # Fecha de primera publicación
            y, m = _normalize_date(rg.get("first-release-date"))
            out["year"] = out.get("year") or y
            out["month"] = out.get("month") or (m or None)

        # Si falta fecha, intentar desde recording (algunas veces viene 'first-release-date' allí también)
        if not out.get("year"):
            y, m = _normalize_date(recs[0].get("first-release-date") if recs else None)
            out["year"] = y or out.get("year")
            out["month"] = out.get("month") or (m or None)

        # 3) Género desde MusicBrainz (si se pudo configurar)
        if use_mb and out.get("mb_recording_id"):
            g = _get_genre_from_mb_recording(out["mb_recording_id"])
            if g:
                out["genre"] = g

        # Limpieza mínima: si mes no está, no forzar "00" aquí (eso lo decide el planner)
        return {k: v for k, v in out.items() if v}
    except Exception as e:
        logger.debug(f"Enriquecimiento MB/AcoustID falló: {e}")
        return {}
