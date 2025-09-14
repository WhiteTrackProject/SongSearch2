import os

APP_NAME = "SongSearch"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "songsearch.db")

# Extensiones soportadas
FILE_EXTS = {".mp3", ".flac", ".wav", ".aiff", ".ogg", ".aac", ".m4a", ".mp4"}

# Fuzzy por defecto
DEFAULT_FUZZY_THRESHOLD = 70  # 0-100

# Plantilla Organizer
DEFAULT_DEST_TEMPLATE = "{year}/{month}/{genre}/{artist}/{artist} - {title}{ext}"


# --- MusicBrainz / AcoustID config ---
MB_APP_NAME = APP_NAME
MB_APP_VERSION = "1.0"
MB_CONTACT = ""  # opcional: tu email o url de proyecto para cortesía

# AcoustID API key: obtén una en https://acoustid.org/api-key
# Puedes ponerla aquí en texto plano o leerla de entorno con os.environ.get("ACOUSTID_API_KEY")
ACOUSTID_API_KEY = os.environ.get("ACOUSTID_API_KEY", "")  # <- pon aquí tu key si prefieres

