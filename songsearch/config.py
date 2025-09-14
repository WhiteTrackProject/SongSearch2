import os

APP_NAME = "SongSearch"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
DB_PATH = os.path.join(DATA_DIR, "songsearch.db")

# Extensiones soportadas
FILE_EXTS = {".mp3", ".flac", ".wav", ".aiff", ".ogg", ".aac", ".m4a", ".mp4"}

# Fuzzy por defecto
DEFAULT_FUZZY_THRESHOLD = 70  # 0-100

# Plantilla Organizer
DEFAULT_DEST_TEMPLATE = "{year}/{month}/{genre}/{artist}/{artist} - {title}{ext}"

# --- MusicBrainz / AcoustID config ---
# ``musicbrainzngs`` and ``pyacoustid`` require a user-agent string and
# optionally an API key for AcoustID lookups.  The defaults below mirror the
# previous ``src`` package so that older configurations continue to work.
MB_APP_NAME = APP_NAME
MB_APP_VERSION = "1.0"
MB_CONTACT = ""  # e.g. your email or project URL (optional courtesy)

# AcoustID API key.  Can also be provided via the ``ACOUSTID_API_KEY``
# environment variable; the configuration value is used as a fallback.
ACOUSTID_API_KEY = os.environ.get("ACOUSTID_API_KEY", "")


def init_paths() -> None:
    """Create required application directories.

    Ensures that :data:`DATA_DIR` exists before components such as the
    database attempt to use it.  This avoids performing filesystem
    operations at import time.
    """

    os.makedirs(DATA_DIR, exist_ok=True)

