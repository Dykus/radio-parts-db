# main.py
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication, QTranslator, QLocale

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

    # Попытка загрузить русский перевод для стандартных диалогов Qt
    translator = QTranslator()
    if translator.load(QLocale(QLocale.Russian, QLocale.Russia), "qt", "_", ":/translations"):
        app.installTranslator(translator)
    else:
        import os
        qt_translations_path = os.path.join(os.path.dirname(sys.executable), "translations", "qt_ru.qm")
        if os.path.exists(qt_translations_path) and translator.load(qt_translations_path):
            app.installTranslator(translator)

    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    db = Database(DB_PATH)
    db.init_schema()

    window = MainWindow(db)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()