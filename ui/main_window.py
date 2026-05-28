# ui/main_window.py
import os
import logging
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLineEdit, QStatusBar, QLabel, QMessageBox, QFileDialog, QMenuBar, QComboBox, QMenu, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QShortcut, QKeySequence

from ui.dialogs.part_dialog import PartDialog
from ui.dialogs.batch_edit_dialog import BatchEditDialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.part_viewer import PartViewer
from ui.widgets.parts_table import PartsTableWidget
from ui.widgets.info_panel import InfoPanelWidget
from ui.widgets.category_tree import CategoryTreeWidget
from config import APP_NAME, APP_VERSION

logger = logging.getLogger(__name__)
from core.database import Database
from utils.importer import import_csv

SETTINGS_FILE = "window_settings.json"

class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle(f" {APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1200, 700)
        self.current_filter = "all"
        self.selected_location_path = None
        self.selected_category_id = None
        
        self._load_window_settings()
        self.category_tree_depth = self.saved_settings.get('category_tree_depth', 0)
        self.location_tree_depth = self.saved_settings.get('location_tree_depth', 0)
        self.selector_tree_depth = self.saved_settings.get('selector_tree_depth', 0)
        
        self._init_ui()
        self._apply_saved_settings()
        self._refresh_all()
    
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
                'maximized': self.isMaximized(),
                'geometry': [self.geometry().x(), self.geometry().y(), self.width(), self.height()],
                'main_splitter_sizes': self.main_splitter.sizes(),
                'table_column_widths': [self.parts_table.table_view.horizontalHeader().sectionSize(i) for i in range(8)],
                'table_column_order': self.parts_table.get_column_order(),
                'category_tree_depth': self.category_tree_depth,
                'location_tree_depth': self.location_tree_depth,
                'selector_tree_depth': self.selector_tree_depth
            }
            # Добавляем токен, если он есть в saved_settings
            if 'yandex_token' in self.saved_settings:
                settings['yandex_token'] = self.saved_settings['yandex_token']
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            logger.info(f" Настройки сохранены в {SETTINGS_FILE}")
        except Exception as e:
            logger.warning(f"Ошибка сохранения настроек: {e}")

    def _save_token(self, token):
        """Сохраняет токен Яндекс.Диска в отдельном файле или в настройках."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
            else:
                settings = {}
            settings['yandex_token'] = token
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            logger.info(f" Токен сохранён в {SETTINGS_FILE}")
        except Exception as e:
            logger.warning(f"Ошибка сохранения токена: {e}")

    def _apply_saved_settings(self):
        if not self.saved_settings:
            return
        if self.saved_settings.get('maximized', False):
            self.showMaximized()
        else:
            geom = self.saved_settings.get('geometry')
            if geom and len(geom) == 4:
                self.setGeometry(geom[0], geom[1], geom[2], geom[3])
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
        if 'table_column_order' in self.saved_settings:
            self.parts_table.set_column_order(self.saved_settings['table_column_order'])

    def closeEvent(self, event):
        self._save_window_settings()
        super().closeEvent(event)

    def resizeEvent(self, event):
        self._save_window_settings()
        super().resizeEvent(event)

    def moveEvent(self, event):
        self._save_window_settings()
        super().moveEvent(event)

    def _init_ui(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("Файл")
        
        import_action = QAction("📥 Импорт CSV", self)
        import_action.triggered.connect(self._import_csv)
        file_menu.addAction(import_action)
        
        export_menu = QMenu("📤 Экспорт", self)
        export_csv_action = QAction("CSV файл (*.csv)", self)
        export_csv_action.triggered.connect(lambda: self._export_data("csv"))
        export_excel_action = QAction("Excel файл (*.xlsx)", self)
        export_excel_action.triggered.connect(lambda: self._export_data("excel"))
        export_menu.addAction(export_csv_action)
        export_menu.addAction(export_excel_action)
        file_menu.addMenu(export_menu)
        
        file_menu.addSeparator()
        
        backup_action = QAction("📤 Выгрузить резервную копию в Яндекс.Диск", self)
        backup_action.triggered.connect(self._backup_to_cloud)
        file_menu.addAction(backup_action)
        
        restore_action = QAction("📥 Восстановить из резервной копии (Яндекс.Диск)", self)
        restore_action.triggered.connect(self._restore_from_cloud)
        file_menu.addAction(restore_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction("⚙️ Настройки", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        help_menu = menubar.addMenu("Помощь")
        help_action = QAction("❓ Помощь", self)
        help_action.triggered.connect(self._open_help)
        help_menu.addAction(help_action)
        
        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

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
        
        self.batch_edit_btn = QPushButton("✏️ Пакетное редактирование")
        self.batch_edit_btn.setEnabled(False)
        self.batch_edit_btn.clicked.connect(self._batch_edit)
        
        self.filter_all_btn = QPushButton(" Все")
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
        
        for w in [self.add_btn, self.edit_btn, self.del_btn, self.batch_edit_btn, QLabel("|"),
                  self.filter_all_btn, self.filter_stock_btn, self.filter_low_btn, self.filter_out_btn]:
            toolbar.addWidget(w)
        toolbar.addStretch()
        toolbar.addWidget(self.search_edit)
        main_layout.addLayout(toolbar)
        
        self.main_splitter = QSplitter(Qt.Horizontal)
        
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
        self.category_depth_inline.currentIndexChanged.connect(self._on_category_depth_changed)
        left_layout.addWidget(self.category_depth_inline)
        
        self.category_tree = CategoryTreeWidget(self.db, start_depth=self.category_tree_depth)
        self.category_tree.category_selected.connect(self._on_category_selected)
        self.category_tree.categories_changed.connect(self._refresh_all)
        left_layout.addWidget(self.category_tree)
        self.main_splitter.addWidget(left_panel)
        
        self.parts_table = PartsTableWidget(self.db)
        self.parts_table.selection_changed.connect(self._on_selection_changed)
        self.parts_table.double_clicked.connect(self._view_part)
        self.parts_table.selection_changed_batch.connect(self._on_batch_selection_changed)
        self.main_splitter.addWidget(self.parts_table)
        
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
        self.location_depth_inline.currentIndexChanged.connect(self._on_location_depth_changed)
        right_layout.addWidget(self.location_depth_inline)
        
        self.right_panel = InfoPanelWidget(self.db, start_depth=self.location_tree_depth)
        self.right_panel.location_clicked.connect(self._filter_by_location)
        self.right_panel.depth_changed.connect(self._on_location_depth_from_widget)
        right_layout.addWidget(self.right_panel)
        self.main_splitter.addWidget(right_panel)
        
        self.main_splitter.setSizes([250, 700, 300])
        main_layout.addWidget(self.main_splitter)
        
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._update_status()

        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._add_part)
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self._edit_part)
        QShortcut(QKeySequence("Del"), self).activated.connect(self._delete_part)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self._focus_search)
        QShortcut(QKeySequence("F5"), self).activated.connect(self._refresh_all)

    # ---- Обработчики глубины ----
    def _on_category_depth_changed(self, index):
        depth = self.category_depth_inline.currentData()
        self.category_tree_depth = depth
        self.category_tree.start_depth = depth
        self.category_tree.load_categories()
        self.saved_settings['category_tree_depth'] = depth
        self._save_window_settings()

    def _on_location_depth_changed(self, index):
        depth = self.location_depth_inline.currentData()
        self.location_tree_depth = depth
        self.right_panel.start_depth = depth
        self.right_panel.load_tree()
        self.saved_settings['location_tree_depth'] = depth
        self._save_window_settings()

    def _on_location_depth_from_widget(self, depth):
        self.location_tree_depth = depth
        self.saved_settings['location_tree_depth'] = depth
        idx = self.location_depth_inline.findData(depth)
        if idx >= 0: self.location_depth_inline.setCurrentIndex(idx)
        self._save_window_settings()

    # ---- Настройки, помощь, о программе ----
    def _open_settings(self):
        dialog = SettingsDialog(self, settings=self.saved_settings)
        dialog.category_depth_changed.connect(self._on_category_depth_from_settings)
        dialog.location_depth_changed.connect(self._on_location_depth_from_settings)
        dialog.selector_depth_changed.connect(self._on_selector_depth_from_settings)
        if dialog.exec():
            new_settings = dialog.get_settings()
            self.saved_settings.update(new_settings)
            self.category_tree_depth = new_settings.get('category_tree_depth', 0)
            self.location_tree_depth = new_settings.get('location_tree_depth', 0)
            self.selector_tree_depth = new_settings.get('selector_tree_depth', 0)
            self._save_window_settings()
            self.category_depth_inline.setCurrentIndex(self.category_depth_inline.findData(self.category_tree_depth))
            self.location_depth_inline.setCurrentIndex(self.location_depth_inline.findData(self.location_tree_depth))
            QMessageBox.information(self, "✅", "Настройки сохранены!")

    def _on_category_depth_from_settings(self, depth):
        self.category_tree_depth = depth
        self.category_tree.start_depth = depth
        self.category_tree.load_categories()

    def _on_location_depth_from_settings(self, depth):
        self.location_tree_depth = depth
        self.right_panel.start_depth = depth
        self.right_panel.load_tree()

    def _on_selector_depth_from_settings(self, depth):
        self.selector_tree_depth = depth

    def _open_help(self):
        from ui.dialogs.help_dialog import HelpDialog
        dialog = HelpDialog(self)
        dialog.exec()

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    # ---- Фильтры и обновления ----
    def _apply_filter(self, filter_type):
        self.current_filter = filter_type
        for btn in [self.filter_all_btn, self.filter_stock_btn, self.filter_low_btn, self.filter_out_btn]: 
            btn.setChecked(False)
        if filter_type == "all": self.filter_all_btn.setChecked(True)
        elif filter_type == "in_stock": self.filter_stock_btn.setChecked(True)
        elif filter_type == "low_stock": self.filter_low_btn.setChecked(True)
        elif filter_type == "out_of_stock": self.filter_out_btn.setChecked(True)
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

    def _refresh_all(self): 
        self.category_tree.load_categories()
        self.right_panel.load_tree()
        self._refresh_table()
        self._update_status()

    def _refresh_table(self): 
        self.parts_table.load_data(self.selected_category_id, self.current_filter, self.selected_location_path)

    def _filter_table(self, text): 
        self.parts_table.proxy_model.set_search_text(text)

    def _focus_search(self):
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def _update_status(self):
        s = self.db.get_stats()
        loc = self.selected_location_path or "Везде"
        cat_text = "Все" if self.selected_category_id is None else "Категория"
        self.status.showMessage(f"📦 {s['total_parts']} | 💰 {s['total_value']:.0f}₽ | 📍 {loc} | 🏷 {cat_text}")

    # ---- Добавление, редактирование, удаление, импорт, экспорт, пакетное редактирование ----
    def _add_part(self):
        dialog = PartDialog(self, db=self.db, start_depth=self.selector_tree_depth)
        if dialog.exec():
            self.db.create_part(dialog.get_data())
            self._refresh_all()
            QMessageBox.information(self, "✅", "Добавлено!")

    def _edit_part(self):
        pid = self.parts_table.get_selected_part_id()
        if pid:
            part = self.db.get_part(pid)
            if part:
                dialog = PartDialog(self, part_data=part, db=self.db, start_depth=self.selector_tree_depth)
                if dialog.exec():
                    self.db.update_part(pid, dialog.get_data())
                    self._refresh_all()
                    QMessageBox.information(self, "✅", "Обновлено!")
        else:
            QMessageBox.warning(self, "⚠️", "Выберите строку")

    def _view_part(self, part_id):
        part = self.db.get_part(part_id)
        if part:
            viewer = PartViewer(part, self.db, self)
            viewer.show()

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

    def _export_data(self, format_type="csv"):
        cat_id = self.selected_category_id
        filter_type = self.current_filter
        loc_path = self.selected_location_path
        parts = self.db.get_all_parts_filtered(category_id=cat_id, filter_type=filter_type, location_path=loc_path)
        categories = {c[0]: c[1] for c in self.db.get_categories()}
        for p in parts:
            p['category_name'] = categories.get(p.get('category_id'), '')
            p['description'] = p.get('notes', '')
            if p.get('value_numeric') is None:
                p['value_numeric'] = ''
        if not parts:
            QMessageBox.information(self, "Экспорт", "Нет данных для экспорта.")
            return

        if format_type == "csv":
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", "", "CSV файл (*.csv)")
            if not file_path:
                return
            try:
                from utils.exporter import export_to_csv
                count = export_to_csv(parts, Path(file_path))
                QMessageBox.information(self, "Экспорт", f"Экспортировано {count} деталей в CSV.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить CSV:\n{e}")
        else:
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить Excel", "", "Excel файл (*.xlsx)")
            if not file_path:
                return
            try:
                from utils.exporter import export_to_excel
                count = export_to_excel(parts, Path(file_path))
                QMessageBox.information(self, "Экспорт", f"Экспортировано {count} деталей в Excel.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить Excel:\n{e}")

    def _on_batch_selection_changed(self, count):
        self.batch_edit_btn.setEnabled(count >= 2)

    def _batch_edit(self):
        part_ids = self.parts_table.get_selected_part_ids()
        if len(part_ids) < 2:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы две детали для пакетного редактирования.")
            return
        dialog = BatchEditDialog(self, part_ids, self.db)
        if dialog.exec():
            self._refresh_all()
            QMessageBox.information(self, "Готово", f"Обновлено {len(part_ids)} деталей.")

    # ---- Резервное копирование через Яндекс.Диск ----
    def _get_yandex_token(self):
        token = self.saved_settings.get('yandex_token')
        if not token:
            from utils.cloud_backup import YandexDiskBackup
            token = YandexDiskBackup.request_token_interactive(self)
            if token:
                self.saved_settings['yandex_token'] = token
                self._save_token(token)
        return token

    def _backup_to_cloud(self):
        token = self._get_yandex_token()
        if not token:
            QMessageBox.warning(self, "Нет токена", "Не удалось получить токен. Резервное копирование отменено.")
            return

        from utils.cloud_backup import YandexDiskBackup
        backup = YandexDiskBackup(token)
        if not backup.is_authenticated():
            QMessageBox.critical(self, "Ошибка", "Не удалось авторизоваться. Проверьте токен.")
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            zip_path = backup.create_backup_zip()
            if backup.upload_backup(zip_path):
                QMessageBox.information(self, "Готово", "Резервная копия успешно загружена в Яндекс.Диск.\nПуть: /RadioPartsDB/backups")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось загрузить архив.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании архива: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _restore_from_cloud(self):
        reply = QMessageBox.warning(self, "Восстановление данных",
            "⚠️ ВНИМАНИЕ! Восстановление заменит текущую базу данных, изображения и даташиты.\n\n"
            "Перед восстановлением закройте программу (это окно) и убедитесь, что RadioPartsDB не запущена.\n"
            "Если программа открыта, закройте её сейчас.\n\n"
            "Продолжить?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        token = self._get_yandex_token()
        if not token:
            QMessageBox.warning(self, "Нет токена", "Не удалось получить токен.")
            return

        from utils.cloud_backup import YandexDiskBackup
        backup = YandexDiskBackup(token)
        if not backup.is_authenticated():
            QMessageBox.critical(self, "Ошибка", "Авторизация не удалась.")
            return

        backups = backup.list_backups()
        if not backups:
            QMessageBox.information(self, "Нет копий", "В облаке не найдено резервных копий.")
            return

        latest = backups[0]
        reply = QMessageBox.question(self, "Подтверждение",
            f"Будет восстановлена копия:\n{latest['name']}\nДата: {latest['modified']}\n\nПродолжить?",
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            import tempfile
            zip_path = Path(tempfile.gettempdir()) / latest['name']
            if backup.download_backup(latest['path'], zip_path):
                if backup.restore_from_zip(zip_path):
                    QMessageBox.information(self, "Успешно", "Данные восстановлены. Перезапустите программу.")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось восстановить данные.")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось скачать архив.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {e}")
        finally:
            QApplication.restoreOverrideCursor()