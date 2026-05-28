# config.py
import os
from pathlib import Path

APP_NAME = "RadioPartsDB"
APP_VERSION = "0.21.3"

# Пути к данным
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "radioparts.db"
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# Настройки автобэкапа
ENABLE_AUTO_BACKUP = True
BACKUP_COUNT = 5