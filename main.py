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
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)  # можно оставить, deprecated, но работает
    app = QApplication(sys.argv)

    # Принудительно устанавливаем светлую тему (серый фон, чёрный текст)
    app.setStyleSheet("""
        /* Общие настройки */
        QWidget {
            background-color: #f0f0f0;
            color: #000000;
        }
        /* Панели инструментов, меню */
        QMenuBar {
            background-color: #e0e0e0;
            color: #000000;
        }
        QMenuBar::item:selected {
            background-color: #c0c0c0;
        }
        QMenu {
            background-color: #f0f0f0;
            color: #000000;
        }
        QMenu::item:selected {
            background-color: #3399ff;
            color: #ffffff;
        }
        /* Кнопки */
        QPushButton {
            background-color: #e0e0e0;
            color: #000000;
            border: 1px solid #a0a0a0;
            border-radius: 4px;
            padding: 4px 8px;
        }
        QPushButton:hover {
            background-color: #d0d0d0;
        }
        QPushButton:pressed {
            background-color: #c0c0c0;
        }
        QPushButton:disabled {
            background-color: #e0e0e0;
            color: #808080;
        }
        /* Поля ввода */
        QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateTimeEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #a0a0a0;
            border-radius: 3px;
            padding: 2px;
        }
        QComboBox::drop-down {
            border: none;
        }
        /* Таблицы */
        QTableView {
            background-color: #ffffff;
            color: #000000;
            gridline-color: #d0d0d0;
        }
        QHeaderView::section {
            background-color: #e0e0e0;
            color: #000000;
            padding: 4px;
            border: 1px solid #d0d0d0;
        }
        QTableCornerButton::section {
            background-color: #e0e0e0;
        }
        /* Деревья */
        QTreeView {
            background-color: #ffffff;
            color: #000000;
        }
        QTreeView::item:hover {
            background-color: #e0e0e0;
        }
        QTreeView::item:selected {
            background-color: #3399ff;
            color: #ffffff;
        }
        /* Статус бар */
        QStatusBar {
            background-color: #e0e0e0;
            color: #000000;
        }
        /* Группы */
        QGroupBox {
            background-color: #f0f0f0;
            color: #000000;
            border: 1px solid #c0c0c0;
            border-radius: 5px;
            margin-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            background-color: #f0f0f0;
            color: #000000;
        }
        /* Вкладки */
        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: #f0f0f0;
        }
        QTabBar::tab {
            background-color: #e0e0e0;
            color: #000000;
            padding: 4px 8px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #f0f0f0;
        }
        QTabBar::tab:hover {
            background-color: #d0d0d0;
        }
        /* ScrollArea */
        QScrollArea {
            background-color: #f0f0f0;
            border: none;
        }
        /* Модальные окна */
        QDialog {
            background-color: #f0f0f0;
        }
    """)

    # Загрузка перевода (если есть)
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