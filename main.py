# main.py
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication

sys.path.insert(0, str(Path(__file__).parent))

from config import APP_NAME, APP_VERSION, DB_PATH, DATA_DIR
from core.database import Database
from ui.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(DATA_DIR / "app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def main():
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    db = Database(DB_PATH)
    db.init_schema()

    window = MainWindow(db)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()