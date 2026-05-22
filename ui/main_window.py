# ui/main_window.py
import os
import logging
import json
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLineEdit, QStatusBar, QLabel, QMessageBox, QFileDialog, QMenuBar
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QStandardItemModel, QAction

from ui.dialogs.part_dialog import PartDialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.widgets.parts_table import PartsTableWidget
from ui.widgets.info_panel import InfoPanelWidget
from ui.widgets.category_tree import CategoryTreeWidget

logger = logging.getLogger(__name__)
from core.database import Database
from utils.importer import import_csv

SETTINGS_FILE = "window_settings.json"

class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle("📦 RadioPartsDB v0.16.0")
        self.setMinimumSize(1200, 700)
        self.current_filter = "all"
        self.selected_location_path = None
        self.selected_category_id = None
        
        self._load_window_settings()
        self.category_tree_depth = self.saved_settings.get('category_tree_depth', 0)
        self.location_tree_depth = self.saved_settings.get('location_tree_depth', 0)
        
        self._init_ui()
        self._refresh_all()
        self._apply_saved_settings()
    
    def _load_window_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f: 
                    self.saved_settings = json.load(f)
                logger.info(f"✅ Загружены настройки из {SETTINGS_FILE}")
            except Exception as e: 
                logger.warning(f"Ошибка загрузки настроек: {e}")
                self.saved_settings = {}
        else: 
            self.saved_settings = {}

    def _save_window_settings(self):
        try:
            settings = {
                'geometry': [self.geometry().x(), self.geometry().y(), self.width(), self.height()],
                'main_splitter_sizes': self.main_splitter.sizes(),
                'table_column_widths': [self.parts_table.table_view.horizontalHeader().sectionSize(i) for i in range(8)],
                'category_tree_depth': self.category_tree_depth,
                'location_tree_depth': self.location_tree_depth
            }
            with open(SETTINGS_FILE, 'w') as f: 
                json.dump(settings, f, indent=2)
            logger.info(f"💾 Настройки сохранены в {SETTINGS_FILE}")
        except Exception as e: 
            logger.warning(f"Ошибка сохранения настроек: {e}")

    def _apply_saved_settings(self):
        if not self.saved_settings: 
            return
        if 'main_splitter_sizes' in self.saved_settings:
            sizes = self.saved_settings['main_splitter_sizes']
            if len(sizes) == 3 and all(s > 0 for s in sizes): 
                self.main_splitter.setSizes(sizes)
        if 'table_column_widths' in self.saved_settings:
            widths = self.saved_settings['table_column_widths']
            header = self.parts_table.table_view.horizontalHeader()
            for i, width in enumerate(widths):
                if width > 0: 
                    header.resizeSection(i, width)

    def closeEvent(self, event): 
        self._save_window_settings()
        super().closeEvent(event)

    def _init_ui(self):
        # === Меню бар ===
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("⚙️ Настройки")
        
        action_open_settings = QAction("Открыть настройки...", self)
        action_open_settings.triggered.connect(self._open_settings)
        settings_menu.addAction(action_open_settings)

        # === Основной UI ===
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self._add_part)
        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.clicked.connect(self._edit_part)
        self.del_btn = QPushButton("🗑️ Удалить")
        self.del_btn.clicked.connect(self._delete_part)
        self.import_btn = QPushButton("📥 Импорт CSV")
        self.import_btn.clicked.connect(self._import_csv)
        
        self.filter_all_btn = QPushButton("📋 Все")
        self.filter_all_btn.setCheckable(True)
        self.filter_all_btn.setChecked(True)
        self.filter_all_btn.clicked.connect(self._on_all_filter)
        self.filter_stock_btn = QPushButton("✅ В наличии")
        self.filter_stock_btn.setCheckable(True)
        self.filter_stock_btn.clicked.connect(lambda: self._apply_filter("in_stock"))
        self.filter_low_btn = QPushButton("⚠️ Мало")
        self.filter_low_btn.setCheckable(True)
        self.filter_low_btn.clicked.connect(lambda: self._apply_filter("low_stock"))
        self.filter_out_btn = QPushButton("❌ Нет")
        self.filter_out_btn.setCheckable(True)
        self.filter_out_btn.clicked.connect(lambda: self._apply_filter("out_of_stock"))
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск...")
        self.search_edit.textChanged.connect(self._filter_table)
        
        for w in [self.add_btn, self.edit_btn, self.del_btn, self.import_btn, QLabel("|"), 
                  self.filter_all_btn, self.filter_stock_btn, self.filter_low_btn, self.filter_out_btn]: 
            toolbar.addWidget(w)
        toolbar.addStretch()
        toolbar.addWidget(self.search_edit)
        main_layout.addLayout(toolbar)
        
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        self.category_tree = CategoryTreeWidget(self.db, start_depth=self.category_tree_depth)
        self.category_tree.category_selected.connect(self._on_category_selected)
        self.category_tree.categories_changed.connect(self._refresh_all)
        self.main_splitter.addWidget(self.category_tree)
        
        self.parts_table = PartsTableWidget(self.db)
        self.parts_table.selection_changed.connect(self._on_selection_changed)
        self.parts_table.double_clicked.connect(self._edit_part_by_id)
        self.main_splitter.addWidget(self.parts_table)
        
        self.right_panel = InfoPanelWidget(self.db, start_depth=self.location_tree_depth)
        self.right_panel.location_clicked.connect(self._filter_by_location)
        self.main_splitter.addWidget(self.right_panel)
        
        self.main_splitter.setSizes([250, 700, 300])
        main_layout.addWidget(self.main_splitter)
        
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._update_status()

    def _open_settings(self):
        dialog = SettingsDialog(self, settings=self.saved_settings)
        if dialog.exec():
            new_settings = dialog.get_settings()
            self.saved_settings.update(new_settings)
            self.category_tree_depth = new_settings.get('category_tree_depth', 0)
            self.location_tree_depth = new_settings.get('location_tree_depth', 0)
            self._save_window_settings()
            
            self.category_tree.start_depth = self.category_tree_depth
            self.category_tree.load_categories()
            self.right_panel.start_depth = self.location_tree_depth
            self.right_panel.load_tree()
            
            QMessageBox.information(self, "✅", "Настройки сохранены и применены!")

    def _apply_filter(self, filter_type):
        self.current_filter = filter_type
        for btn in [self.filter_all_btn, self.filter_stock_btn, self.filter_low_btn, self.filter_out_btn]: 
            btn.setChecked(False)
        if filter_type == "all": 
            self.filter_all_btn.setChecked(True)
        elif filter_type == "in_stock": 
            self.filter_stock_btn.setChecked(True)
        elif filter_type == "low_stock": 
            self.filter_low_btn.setChecked(True)
        elif filter_type == "out_of_stock": 
            self.filter_out_btn.setChecked(True)
        self._refresh_table()
        self._update_status()

    def _on_all_filter(self): 
        self.selected_category_id = None
        self.category_tree._on_show_all_clicked()
        self._apply_filter("all")

    def _on_category_selected(self, cat_id): 
        self.selected_category_id = cat_id
        self._refresh_table()
        self._update_status()

    def _on_selection_changed(self, part_id):
        if not part_id: 
            self.right_panel.update_content(None)
            return
        part = self.db.get_part(part_id)
        if part: 
            self.right_panel.update_content(part)

    def _filter_by_location(self, location_path): 
        self.selected_location_path = location_path
        self._refresh_table()
        self._update_status()

    def _edit_part_by_id(self, part_id):
        part = self.db.get_part(part_id)
        if part:
            dialog = PartDialog(self, part_data=part, db=self.db)
            if dialog.exec():
                self.db.update_part(part_id, dialog.get_data())
                self._refresh_all()
                QMessageBox.information(self, "✅", "Обновлено!")

    def _refresh_all(self): 
        self.category_tree.load_categories()
        self.right_panel.load_tree()
        self._refresh_table()
        self._update_status()

    def _refresh_table(self): 
        self.parts_table.load_data(self.selected_category_id, self.current_filter, self.selected_location_path)

    def _filter_table(self, text): 
        self.parts_table.proxy_model.set_search_text(text)

    def _update_status(self):
        s = self.db.get_stats()
        loc = self.selected_location_path or "Везде"
        cat_text = "Все" if self.selected_category_id is None else "Категория"
        self.status.showMessage(f"📦 {s['total_parts']} | 💰 {s['total_value']:.0f}₽ | 📍 {loc} | 🏷 {cat_text}")

    def _add_part(self):
        dialog = PartDialog(self, db=self.db)
        if dialog.exec():
            self.db.create_part(dialog.get_data())
            self._refresh_all()
            QMessageBox.information(self, "✅", "Добавлено!")

    def _edit_part(self):
        pid = self.parts_table.get_selected_part_id()
        if pid: 
            self._edit_part_by_id(pid)
        else: 
            QMessageBox.warning(self, "⚠️", "Выберите строку")

    def _delete_part(self):
        pid = self.parts_table.get_selected_part_id()
        if not pid: 
            return
        name = self.db.get_part(pid)['name']
        if QMessageBox.question(self, "❓", f"Удалить '{name}'?") == QMessageBox.Yes:
            self.db.delete_part(pid)
            self._refresh_all()
            QMessageBox.information(self, "✅", "Удалено")

    def _import_csv(self):
        f, _ = QFileDialog.getOpenFileName(self, "CSV", "", "CSV (*.csv)")
        if f:
            try:
                imp, err = import_csv(self.db, f)
                self._refresh_all()
                QMessageBox.information(self, "Импорт", f"Добавлено: {imp}, Ошибок: {err}")
            except Exception as e: 
                QMessageBox.critical(self, "Ошибка", str(e))