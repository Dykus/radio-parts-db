# ui/main_window.py
import os
import logging
import json
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLineEdit, QStatusBar, QLabel, QMessageBox, QFileDialog, QApplication
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QStandardItemModel, QStandardItem

from ui.dialogs.part_dialog import PartDialog
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
        self.setWindowTitle("📦 RadioPartsDB v0.11.0")
        self.setMinimumSize(1200, 700)
        self.current_filter = "all"
        self.selected_location_path = None
        self.selected_category_id = None
        
        self._load_window_settings()
        self._init_ui()
        self._refresh_all()
    
    def _load_window_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    geom = json.load(f).get('geometry')
                    if geom: self.setGeometry(QRect(*geom))
            except Exception as e: logger.warning(f"Ошибка загрузки настроек: {e}")

    def _save_window_settings(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump({'geometry': [self.geometry().x(), self.geometry().y(), self.width(), self.height()]}, f)
        except Exception as e: logger.warning(f"Ошибка сохранения настроек: {e}")

    def closeEvent(self, event):
        self._save_window_settings()
        super().closeEvent(event)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # --- Toolbar ---
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить"); self.add_btn.clicked.connect(self._add_part)
        self.edit_btn = QPushButton("✏️ Редактировать"); self.edit_btn.clicked.connect(self._edit_part)
        self.del_btn = QPushButton("🗑️ Удалить"); self.del_btn.clicked.connect(self._delete_part)
        self.import_btn = QPushButton("📥 Импорт CSV"); self.import_btn.clicked.connect(self._import_csv)
        
        self.filter_all_btn = QPushButton("📋 Все"); self.filter_all_btn.setCheckable(True); self.filter_all_btn.setChecked(True); self.filter_all_btn.clicked.connect(self._on_all_filter)
        self.filter_stock_btn = QPushButton("✅ В наличии"); self.filter_stock_btn.setCheckable(True); self.filter_stock_btn.clicked.connect(lambda: self._apply_filter("in_stock"))
        self.filter_low_btn = QPushButton("⚠️ Мало"); self.filter_low_btn.setCheckable(True); self.filter_low_btn.clicked.connect(lambda: self._apply_filter("low_stock"))
        self.filter_out_btn = QPushButton("❌ Нет"); self.filter_out_btn.setCheckable(True); self.filter_out_btn.clicked.connect(lambda: self._apply_filter("out_of_stock"))
        
        self.search_edit = QLineEdit(); self.search_edit.setPlaceholderText("🔍 Поиск..."); self.search_edit.textChanged.connect(self._filter_table)
        
        for w in [self.add_btn, self.edit_btn, self.del_btn, self.import_btn, QLabel("|"), 
                  self.filter_all_btn, self.filter_stock_btn, self.filter_low_btn, self.filter_out_btn]:
            toolbar.addWidget(w)
        toolbar.addStretch()
        toolbar.addWidget(self.search_edit)
        main_layout.addLayout(toolbar)
        
        # --- Main Splitter ---
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 1. Левая панель: Категории
        self.category_tree = CategoryTreeWidget(self.db)
        self.category_tree.category_selected.connect(self._on_category_selected)
        self.category_tree.categories_changed.connect(self._refresh_all)
        main_splitter.addWidget(self.category_tree)
        
        # 2. Центральная панель: Таблица
        self.parts_table = PartsTableWidget(self.db)
        self.parts_table.selection_changed.connect(self._on_selection_changed)
        self.parts_table.double_clicked.connect(self._edit_part_by_id)
        main_splitter.addWidget(self.parts_table)
        
        # 3. Правая панель: Фото + Навигатор
        self.right_panel = InfoPanelWidget(self.db)
        self.right_panel.location_clicked.connect(self._filter_by_location)
        main_splitter.addWidget(self.right_panel)
        
        main_splitter.setSizes([250, 700, 300])
        main_layout.addWidget(main_splitter)
        
        self.status = QStatusBar(); self.setStatusBar(self.status)
        self._update_status()

    def _on_all_filter(self):
        """Кнопка 'Все' сбрасывает и статус, и категорию."""
        self._apply_filter("all")
        self.selected_category_id = None
        self.category_tree._on_show_all_clicked()
        self._refresh_table()
        self._update_status()

    def _apply_filter(self, filter_type):
        self.current_filter = filter_type
        for btn in [self.filter_all_btn, self.filter_stock_btn, self.filter_low_btn, self.filter_out_btn]:
            btn.setChecked(False)
        if filter_type == "all": self.filter_all_btn.setChecked(True)
        elif filter_type == "in_stock": self.filter_stock_btn.setChecked(True)
        elif filter_type == "low_stock": self.filter_low_btn.setChecked(True)
        elif filter_type == "out_of_stock": self.filter_out_btn.setChecked(True)

    def _on_category_selected(self, cat_id):
        self.selected_category_id = cat_id
        self._refresh_table()
        self._update_status()

    def _on_selection_changed(self, part_id):
        if not part_id:
            self.right_panel.update_content(None)
            return
        part = self.db.get_part(part_id)
        if part: self.right_panel.update_content(part)

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
        """Обновляет ВСЕ компоненты: категории, места, таблицу."""
        self.category_tree.load_categories()
        self.right_panel.load_tree()  # ✅ ИСПРАВЛЕНО: Загружаем дерево мест!
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
            d = dialog.get_data()
            cat_name = d['category']
            cid = None
            if cat_name:
                cats = self.db.get_categories()
                cid = next((c[0] for c in cats if c[1] == cat_name), None)
                if not cid: cid = self.db.create_category(cat_name)
            d['category_id'] = cid
            self.db.create_part(d)
            self._refresh_all()
            QMessageBox.information(self, "✅", "Добавлено!")

    def _edit_part(self):
        pid = self.parts_table.get_selected_part_id()
        if pid: self._edit_part_by_id(pid)
        else: QMessageBox.warning(self, "⚠️", "Выберите строку")

    def _delete_part(self):
        pid = self.parts_table.get_selected_part_id()
        if not pid: return
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
                self._refresh_all()  # ✅ Теперь после импорта загрузится и дерево мест
                QMessageBox.information(self, "Импорт", f"Добавлено: {imp}, Ошибок: {err}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))