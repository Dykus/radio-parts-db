# ui/handlers/settings_handler.py
import os
import json
import logging
from PySide6.QtWidgets import QMessageBox
from config import SETTINGS_FILE

logger = logging.getLogger(__name__)

class SettingsHandler:
    def __init__(self, main_window):
        self.main = main_window

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                logger.info(f"✅ Загружены настройки из {SETTINGS_FILE}")
                return settings
            except Exception as e:
                logger.warning(f"Ошибка загрузки настроек: {e}")
        return {}

    def save_settings(self):
        try:
            settings = {
                'maximized': self.main.isMaximized(),
                'geometry': [self.main.geometry().x(), self.main.geometry().y(),
                             self.main.width(), self.main.height()],
                'main_splitter_sizes': self.main.main_splitter.sizes(),
                'table_column_widths': [self.main.parts_table.table_view.horizontalHeader().sectionSize(i) for i in range(8)],
                'table_column_order': self.main.parts_table.get_column_order(),
                'category_tree_depth': self.main.category_tree_depth,
                'location_tree_depth': self.main.location_tree_depth,
                'selector_tree_depth': self.main.selector_tree_depth
            }
            # Сохраняем токен, если есть
            if hasattr(self.main, 'saved_settings') and 'yandex_token' in self.main.saved_settings:
                settings['yandex_token'] = self.main.saved_settings['yandex_token']
            if hasattr(self.main, 'saved_settings') and 'pending_restore' in self.main.saved_settings:
                settings['pending_restore'] = self.main.saved_settings['pending_restore']
            if hasattr(self.main, 'saved_settings') and 'restore_zip_path' in self.main.saved_settings:
                settings['restore_zip_path'] = self.main.saved_settings['restore_zip_path']

            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            logger.info(f" Настройки сохранены в {SETTINGS_FILE}")
        except Exception as e:
            logger.warning(f"Ошибка сохранения настроек: {e}")

    def apply_settings(self, settings):
        if not settings:
            return
        if settings.get('maximized', False):
            self.main.showMaximized()
        else:
            geom = settings.get('geometry')
            if geom and len(geom) == 4:
                self.main.setGeometry(geom[0], geom[1], geom[2], geom[3])
        if 'main_splitter_sizes' in settings:
            sizes = settings['main_splitter_sizes']
            if len(sizes) == 3 and all(s > 0 for s in sizes):
                self.main.main_splitter.setSizes(sizes)
        if 'table_column_widths' in settings:
            widths = settings['table_column_widths']
            header = self.main.parts_table.table_view.horizontalHeader()
            for i, width in enumerate(widths):
                if width > 0:
                    header.resizeSection(i, width)
        if 'table_column_order' in settings:
            self.main.parts_table.set_column_order(settings['table_column_order'])
        # Восстанавливаем токен и другие данные
        self.main.saved_settings = settings