import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.getenv("RADIOPARTS_DATA_DIR", BASE_DIR / "data"))
DB_PATH = DATA_DIR / "radioparts.db"
IMAGES_DIR = DATA_DIR / "images"
DATASHEETS_DIR = DATA_DIR / "datasheets"

APP_NAME = "RadioPartsDB"
APP_VERSION = "0.1.0"
ENABLE_AUTO_BACKUP = True
BACKUP_COUNT = 5

for d in [DATA_DIR, IMAGES_DIR, DATASHEETS_DIR]:
    d.mkdir(parents=True, exist_ok=True)