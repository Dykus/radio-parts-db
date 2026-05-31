# ui/main_window.py
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLineEdit, QStatusBar, QLabel, QMenuBar, QComboBox, QMenu
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QShortcut, QKeySequence

from core.database import Database
from config import APP_NAME, APP_VERSION

from ui.widgets.parts_table import PartsTableWidget
from ui.widgets.info_panel import InfoPanelWidget
from ui.widgets.category_tree import CategoryTreeWidget

from ui.handlers.settings_handler import SettingsHandler
from ui.handlers.selection_handler import SelectionHandler
from ui.actions.file_actions import FileActions
from ui.actions.edit_actions import EditActions
from ui.actions.view_actions import ViewActions

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1200, 700)

        # Инициализация обработчиков
        self.settings_handler = SettingsHandler(self)
        self.selection_handler = SelectionHandler(self)
        self.file_actions = FileActions(self)
        self.edit_actions = EditActions(self)
        self.view_actions = ViewActions(self)

        # Загрузка настроек
        self.saved_settings = self.settings_handler.load_settings()

        # Восстановление параметров окна
        self.category_tree_depth = self.saved_settings.get('category_tree_depth', 0)
        self.location_tree_depth = self.saved_settings.get('location_tree_depth', 0)
        self.selector_tree_depth = self.saved_settings.get('selector_tree_depth', 0)

        # Инициализация UI
        self._init_ui()

        # Применение сохранённых настроек
        self.settings_handler.apply_settings(self.saved_settings)

        # Проверка отложенного восстановления
        self.file_actions.check_pending_restore()

        # Загрузка данных
        self.view_actions.refresh_all()

    def _init_ui(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        help_menu = menubar.addMenu("Помощь")

        # Импорт
        import_action = QAction("📥 Импорт CSV", self)
        import_action.triggered.connect(self.file_actions.import_csv)
        file_menu.addAction(import_action)

        # Экспорт с подменю
        export_menu = QMenu("📤 Экспорт", self)
        export_csv_action = QAction("CSV файл (*.csv)", self)
        export_csv_action.triggered.connect(lambda: self.file_actions.export_data("csv"))
        export_excel_action = QAction("Excel файл (*.xlsx)", self)
        export_excel_action.triggered.connect(lambda: self.file_actions.export_data("excel"))
        export_menu.addAction(export_csv_action)
        export_menu.addAction(export_excel_action)
        file_menu.addMenu(export_menu)

        file_menu.addSeparator()

        backup_action = QAction("📤 Выгрузить резервную копию в Яндекс.Диск", self)
        backup_action.triggered.connect(self.file_actions.backup_to_cloud)
        file_menu.addAction(backup_action)

        restore_action = QAction("📥 Восстановить из резервной копии (Яндекс.Диск)", self)
        restore_action.triggered.connect(self.file_actions.restore_from_cloud)
        file_menu.addAction(restore_action)

        file_menu.addSeparator()

        settings_action = QAction("⚙️ Настройки", self)
        settings_action.triggered.connect(self.view_actions.open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()
        exit_action = QAction("🚪 Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_action = QAction("❓ Помощь", self)
        help_action.triggered.connect(self.view_actions.open_help)
        help_menu.addAction(help_action)

        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self.view_actions.show_about)
        help_menu.addAction(about_action)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Панель инструментов
        toolbar = QHBoxLayout()

        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self.edit_actions.add_part)
        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.clicked.connect(self.edit_actions.edit_part)
        self.del_btn = QPushButton("🗑️ Удалить")
        self.del_btn.clicked.connect(self.edit_actions.delete_part)

        self.batch_edit_btn = QPushButton("✏️ Пакетное редактирование")
        self.batch_edit_btn.setEnabled(False)
        self.batch_edit_btn.clicked.connect(self.edit_actions.batch_edit)

        self.filter_all_btn = QPushButton(" Все")
        self.filter_all_btn.setCheckable(True)
        self.filter_all_btn.setChecked(True)
        self.filter_all_btn.clicked.connect(self.view_actions.on_all_filter)

        self.filter_stock_btn = QPushButton("✅ В наличии")
        self.filter_stock_btn.setCheckable(True)
        self.filter_stock_btn.clicked.connect(lambda: self.view_actions.apply_filter("in_stock"))

        self.filter_low_btn = QPushButton("⚠️ Мало")
        self.filter_low_btn.setCheckable(True)
        self.filter_low_btn.clicked.connect(lambda: self.view_actions.apply_filter("low_stock"))

        self.filter_out_btn = QPushButton("❌ Нет")
        self.filter_out_btn.setCheckable(True)
        self.filter_out_btn.clicked.connect(lambda: self.view_actions.apply_filter("out_of_stock"))

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск...")
        self.search_edit.textChanged.connect(self.view_actions.filter_table)

        for w in [self.add_btn, self.edit_btn, self.del_btn, self.batch_edit_btn, QLabel("|"),
                  self.filter_all_btn, self.filter_stock_btn, self.filter_low_btn, self.filter_out_btn]:
            toolbar.addWidget(w)
        toolbar.addStretch()
        toolbar.addWidget(self.search_edit)
        main_layout.addLayout(toolbar)

        # Основной сплиттер
        self.main_splitter = QSplitter(Qt.Horizontal)

        # Левая панель – категории
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        cat_depth_label = QLabel("📂 Глубина категорий:")
        cat_depth_label.setStyleSheet("font-weight: bold; font-size: 10px;")
        left_layout.addWidget(cat_depth_label)

        self.category_depth_inline = QComboBox()
        self.category_depth_inline.addItem("📁 Полностью свёрнуто", 0)
        self.category_depth_inline.addItem(" Корни + 1 уровень", 1)
        self.category_depth_inline.addItem("📂 Корни + 2 уровня", 2)
        self.category_depth_inline.addItem("📂📂 Корни + 3 уровня", 3)
        self.category_depth_inline.addItem(" Развернуть всё", -1)
        self.category_depth_inline.setCurrentIndex(self.category_depth_inline.findData(self.category_tree_depth))
        self.category_depth_inline.currentIndexChanged.connect(self.view_actions.on_category_depth_changed)
        left_layout.addWidget(self.category_depth_inline)

        self.category_tree = CategoryTreeWidget(self.db, start_depth=self.category_tree_depth)
        self.category_tree.category_selected.connect(self.view_actions.on_category_selected)
        self.category_tree.categories_changed.connect(self.view_actions.refresh_all)
        left_layout.addWidget(self.category_tree)
        self.main_splitter.addWidget(left_panel)

        # Центральная таблица
        self.parts_table = PartsTableWidget(self.db)
        self.parts_table.selection_changed.connect(self.selection_handler.on_selection_changed)
        self.parts_table.double_clicked.connect(self.selection_handler.view_part)
        self.parts_table.selection_changed_batch.connect(self.edit_actions.on_batch_selection_changed)
        self.main_splitter.addWidget(self.parts_table)

        # Правая панель – информация и навигатор
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        loc_depth_label = QLabel("📍 Глубина навигатора:")
        loc_depth_label.setStyleSheet("font-weight: bold; font-size: 10px;")
        right_layout.addWidget(loc_depth_label)

        self.location_depth_inline = QComboBox()
        self.location_depth_inline.addItem("📁 Полностью свёрнуто", 0)
        self.location_depth_inline.addItem("📂 Корни + 1 уровень", 1)
        self.location_depth_inline.addItem("📂 Корни + 2 уровня", 2)
        self.location_depth_inline.addItem(" Корни + 3 уровня", 3)
        self.location_depth_inline.addItem(" Развернуть всё", -1)
        self.location_depth_inline.setCurrentIndex(self.location_depth_inline.findData(self.location_tree_depth))
        self.location_depth_inline.currentIndexChanged.connect(self.view_actions.on_location_depth_changed)
        right_layout.addWidget(self.location_depth_inline)

        self.right_panel = InfoPanelWidget(self.db, start_depth=self.location_tree_depth)
        self.right_panel.location_clicked.connect(self.view_actions.filter_by_location)
        self.right_panel.depth_changed.connect(self.view_actions.on_location_depth_from_widget)
        right_layout.addWidget(self.right_panel)
        self.main_splitter.addWidget(right_panel)

        self.main_splitter.setSizes([250, 700, 300])
        main_layout.addWidget(self.main_splitter)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.view_actions.update_status()

        # Горячие клавиши
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.edit_actions.add_part)
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self.edit_actions.edit_part)
        QShortcut(QKeySequence("Del"), self).activated.connect(self.edit_actions.delete_part)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.view_actions.focus_search)
        QShortcut(QKeySequence("F5"), self).activated.connect(self.view_actions.refresh_all)

    def closeEvent(self, event):
        self.settings_handler.save_settings()
        super().closeEvent(event)

    def resizeEvent(self, event):
        self.settings_handler.save_settings()
        super().resizeEvent(event)

    def moveEvent(self, event):
        self.settings_handler.save_settings()
        super().moveEvent(event)