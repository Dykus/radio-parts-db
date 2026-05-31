# ui/actions/file_actions.py
import tempfile
from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication
from PySide6.QtCore import Qt
from utils.importer import import_csv
from utils.exporter import export_to_csv, export_to_excel
from utils.cloud_backup import YandexDiskBackup

class FileActions:
    def __init__(self, main_window):
        self.main = main_window

    def import_csv(self):
        f, _ = QFileDialog.getOpenFileName(self.main, "CSV", "", "CSV (*.csv)")
        if f:
            try:
                imp, err = import_csv(self.main.db, f)
                self.main.view_actions.refresh_all()
                QMessageBox.information(self.main, "Импорт", f"Добавлено: {imp}, Ошибок: {err}")
            except Exception as e:
                QMessageBox.critical(self.main, "Ошибка", str(e))

    def export_data(self, format_type="csv"):
        cat_id = self.main.view_actions.selected_category_id
        filter_type = self.main.view_actions.current_filter
        loc_path = self.main.view_actions.selected_location_path
        parts = self.main.db.get_all_parts_filtered(category_id=cat_id, filter_type=filter_type, location_path=loc_path)
        categories = {c[0]: c[1] for c in self.main.db.get_categories()}
        for p in parts:
            p['category_name'] = categories.get(p.get('category_id'), '')
            p['description'] = p.get('notes', '')
            if p.get('value_numeric') is None:
                p['value_numeric'] = ''
        if not parts:
            QMessageBox.information(self.main, "Экспорт", "Нет данных для экспорта.")
            return

        if format_type == "csv":
            file_path, _ = QFileDialog.getSaveFileName(self.main, "Сохранить CSV", "", "CSV файл (*.csv)")
            if not file_path:
                return
            try:
                count = export_to_csv(parts, Path(file_path))
                QMessageBox.information(self.main, "Экспорт", f"Экспортировано {count} деталей в CSV.")
            except Exception as e:
                QMessageBox.critical(self.main, "Ошибка", f"Не удалось сохранить CSV:\n{e}")
        else:
            file_path, _ = QFileDialog.getSaveFileName(self.main, "Сохранить Excel", "", "Excel файл (*.xlsx)")
            if not file_path:
                return
            try:
                count = export_to_excel(parts, Path(file_path))
                QMessageBox.information(self.main, "Экспорт", f"Экспортировано {count} деталей в Excel.")
            except Exception as e:
                QMessageBox.critical(self.main, "Ошибка", f"Не удалось сохранить Excel:\n{e}")

    def _get_yandex_token(self):
        token = self.main.saved_settings.get('yandex_token')
        if not token:
            token = YandexDiskBackup.request_token_interactive(self.main)
            if token:
                self.main.saved_settings['yandex_token'] = token
                self.main.settings_handler.save_settings()
        return token

    def backup_to_cloud(self):
        token = self._get_yandex_token()
        if not token:
            QMessageBox.warning(self.main, "Нет токена", "Не удалось получить токен. Резервное копирование отменено.")
            return

        backup = YandexDiskBackup(token)
        if not backup.is_authenticated():
            QMessageBox.critical(self.main, "Ошибка", "Не удалось авторизоваться. Проверьте токен.")
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            zip_path = backup.create_backup_zip()
            if backup.upload_backup(zip_path):
                QMessageBox.information(self.main, "Готово", "Резервная копия успешно загружена в Яндекс.Диск.\nПуть: /RadioPartsDB/backups")
            else:
                QMessageBox.critical(self.main, "Ошибка", "Не удалось загрузить архив.")
        except Exception as e:
            QMessageBox.critical(self.main, "Ошибка", f"Ошибка при создании архива: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def restore_from_cloud(self):
        token = self._get_yandex_token()
        if not token:
            QMessageBox.warning(self.main, "Нет токена", "Не удалось получить токен.")
            return

        backup = YandexDiskBackup(token)
        if not backup.is_authenticated():
            QMessageBox.critical(self.main, "Ошибка", "Авторизация не удалась.")
            return

        backups = backup.list_backups()
        if not backups:
            QMessageBox.information(self.main, "Нет копий", "В облаке не найдено резервных копий.")
            return

        latest = backups[0]
        reply = QMessageBox.question(self.main, "Подтверждение",
            f"Будет загружена и восстановлена копия:\n{latest['name']}\nДата: {latest['modified']}\n\n"
            "Программа будет закрыта. При следующем запуске данные будут восстановлены автоматически.\n\n"
            "Продолжить?",
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        zip_path = Path(tempfile.gettempdir()) / latest['name']
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            if not backup.download_backup(latest['path'], zip_path):
                QMessageBox.critical(self.main, "Ошибка", "Не удалось скачать архив.")
                return
        except Exception as e:
            QMessageBox.critical(self.main, "Ошибка", f"Ошибка скачивания: {e}")
            return
        finally:
            QApplication.restoreOverrideCursor()

        self.main.saved_settings['pending_restore'] = True
        self.main.saved_settings['restore_zip_path'] = str(zip_path)
        self.main.settings_handler.save_settings()

        QMessageBox.information(self.main, "Восстановление", "Программа будет закрыта. При следующем запуске данные будут восстановлены.")
        self.main.close()

    def check_pending_restore(self):
        pending = self.main.saved_settings.get('pending_restore')
        if pending:
            self.main.saved_settings.pop('pending_restore', None)
            restore_zip_path = self.main.saved_settings.pop('restore_zip_path', None)
            self.main.settings_handler.save_settings()

            if not restore_zip_path or not Path(restore_zip_path).exists():
                QMessageBox.critical(self.main, "Ошибка", "Не найден архив для восстановления. Операция отменена.")
                return

            token = self.main.saved_settings.get('yandex_token')
            if not token:
                QMessageBox.critical(self.main, "Ошибка", "Токен не найден. Восстановление невозможно.")
                return

            backup = YandexDiskBackup(token)
            if not backup.is_authenticated():
                QMessageBox.critical(self.main, "Ошибка", "Не удалось авторизоваться. Проверьте токен.")
                return

            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                if backup.restore_from_zip(Path(restore_zip_path)):
                    QMessageBox.information(self.main, "Успешно", "Данные восстановлены.")
                else:
                    QMessageBox.critical(self.main, "Ошибка", "Не удалось восстановить данные.")
            except Exception as e:
                QMessageBox.critical(self.main, "Ошибка", f"Ошибка восстановления: {e}")
            finally:
                QApplication.restoreOverrideCursor()
                try:
                    Path(restore_zip_path).unlink(missing_ok=True)
                except Exception:
                    pass