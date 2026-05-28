# utils/cloud_backup.py
import os
import zipfile
import tempfile
import webbrowser
import shutil
from pathlib import Path
from typing import Optional, List
import yadisk
from PySide6.QtWidgets import QMessageBox, QInputDialog, QApplication
from config import DATA_DIR, DB_PATH

class YandexDiskBackup:
    """Резервное копирование и восстановление через Яндекс.Диск."""

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.y = yadisk.YaDisk(token=token) if token else None

    @staticmethod
    def request_token_interactive(parent=None) -> Optional[str]:
        """Запрашивает токен у пользователя."""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Авторизация в Яндекс.Диске")
        msg.setText("Для работы с резервными копиями необходим токен доступа.\n\n"
                    "1. Перейдите по ссылке:\n   https://yandex.ru/dev/disk/poligon/\n"
                    "2. Нажмите кнопку «Получить токен» (в правом верхнем углу).\n"
                    "3. Разрешите доступ к файлам (кнопка «Разрешить»).\n"
                    "4. Скопируйте полученную строку токена.\n"
                    "5. Нажмите «ОК» и вставьте токен в поле ниже.\n\n"
                    "Токен будет сохранён и использоваться в дальнейшем.")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        open_browser_btn = msg.addButton("🌐 Открыть страницу получения токена", QMessageBox.ActionRole)
        msg.exec()

        if msg.clickedButton() == open_browser_btn:
            webbrowser.open("https://yandex.ru/dev/disk/poligon/")

        token, ok = QInputDialog.getText(parent, "Токен Яндекс.Диска", "Вставьте токен:", text="")
        if ok and token:
            return token.strip()
        return None

    def is_authenticated(self) -> bool:
        return self.y is not None and self.y.check_token()

    def _ensure_remote_dir(self, remote_path: str) -> bool:
        """Проверяет и создаёт каталог на Яндекс.Диске."""
        if not self.is_authenticated():
            return False
        try:
            path = remote_path.strip('/')
            if not path:
                return True
            if self.y.exists(path):
                if not self.y.is_dir(path):
                    print(f"Ошибка: '{remote_path}' - это файл, а не каталог.")
                    return False
                return True
            parts = path.split('/')
            current_path = ''
            for part in parts:
                if not part:
                    continue
                if current_path:
                    current_path += '/' + part
                else:
                    current_path = part
                if not self.y.exists(current_path):
                    print(f"Создаю каталог: /{current_path}")
                    self.y.mkdir(current_path)
            return True
        except Exception as e:
            print(f"Ошибка при создании каталога {remote_path}: {e}")
            return False

    def create_backup_zip(self) -> Path:
        """Создаёт ZIP-архив с БД, изображениями и даташитами."""
        temp_dir = Path(tempfile.gettempdir()) / "radioparts_backup"
        temp_dir.mkdir(exist_ok=True)
        zip_path = temp_dir / f"radioparts_backup_{DB_PATH.stem}.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if DB_PATH.exists():
                zf.write(DB_PATH, arcname=DB_PATH.name)
            for folder in ['images', 'datasheets']:
                folder_path = DATA_DIR / folder
                if folder_path.exists():
                    for file_path in folder_path.rglob('*'):
                        if file_path.is_file():
                            rel_path = file_path.relative_to(DATA_DIR)
                            zf.write(file_path, arcname=str(rel_path))
        return zip_path

    def upload_backup(self, zip_path: Path, remote_dir: str = "/RadioPartsDB/backups") -> bool:
        """Загружает ZIP-архив на Яндекс.Диск."""
        if not self.is_authenticated():
            return False
        if not self._ensure_remote_dir(remote_dir):
            print(f"Не удалось создать или проверить папку: {remote_dir}")
            return False
        remote_path = f"{remote_dir}/{zip_path.name}"
        try:
            self.y.upload(str(zip_path), remote_path, overwrite=True)
            return True
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return False

    def list_backups(self, remote_dir: str = "/RadioPartsDB/backups") -> List[dict]:
        """Возвращает список файлов .zip в облачной папке."""
        if not self.is_authenticated():
            return []
        try:
            items = self.y.listdir(remote_dir)
            backups = []
            for item in items:
                if item.is_file() and item.name.endswith('.zip'):
                    backups.append({
                        'name': item.name,
                        'size': item.size,
                        'modified': item.modified,
                        'path': item.path
                    })
            backups.sort(key=lambda x: x['modified'], reverse=True)
            return backups
        except Exception:
            return []

    def download_backup(self, remote_path: str, local_zip_path: Path) -> bool:
        """Скачивает архив из облака."""
        if not self.is_authenticated():
            return False
        try:
            self.y.download(remote_path, str(local_zip_path))
            return True
        except Exception:
            return False

    def restore_from_zip(self, zip_path: Path) -> bool:
        """Распаковывает архив и заменяет локальные данные."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                extract_dir = Path(tempfile.mkdtemp())
                zf.extractall(extract_dir)

                src_db = extract_dir / DB_PATH.name
                if src_db.exists():
                    backup_db = DATA_DIR / f"{DB_PATH.stem}_before_restore.db"
                    if DB_PATH.exists():
                        shutil.copy2(DB_PATH, backup_db)
                    shutil.copy2(src_db, DB_PATH)

                for folder in ['images', 'datasheets']:
                    src_folder = extract_dir / folder
                    dst_folder = DATA_DIR / folder
                    if src_folder.exists():
                        if dst_folder.exists():
                            shutil.rmtree(dst_folder)
                        shutil.copytree(src_folder, dst_folder)

                shutil.rmtree(extract_dir)
            return True
        except Exception as e:
            print(f"Ошибка восстановления: {e}")
            return False