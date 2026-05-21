# core/database.py
import sqlite3
import json
import shutil
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

# ==============================================================================
# ⚠️ ВАЖНО: ИЗМЕНЕНИЕ СТРУКТУРЫ БАЗЫ ДАННЫХ
# ==============================================================================
# НИКОГДА не меняйте SQL-запросы в init_schema() или в методах CRUD напрямую!
# Для любого изменения схемы (новая колонка, переименование, типы данных):
#   1. Поднимите CURRENT_SCHEMA_VERSION в классе Database (__init__)
#   2. Добавьте функцию миграции в self._migrations[НОВАЯ_ВЕРСИЯ] = ...
#   3. Напишите логику изменения в отдельном методе _migration_vX_описание()
# Программа сама применит изменения при запуске. Данные не пострадают.
# Подробности: см. файл SCHEMA_CHANGES.md в корне проекта.
# ==============================================================================

CURRENT_SCHEMA_VERSION = 2
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._connection = None
        self._migrations = {
            1: self._migration_v1_initial,
            2: self._migration_v2_russian_statuses,
        }

    def connect(self):
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    @contextmanager
    def get_cursor(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка БД: {e}")
            raise
        finally:
            cursor.close()

    def init_schema(self):
        with self.get_cursor() as cursor:
            cursor.execute("""CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            row = cursor.fetchone()
            current_version = row[0] if row else 0

            if current_version >= CURRENT_SCHEMA_VERSION:
                logger.info(f"✅ Схема БД актуальна (версия {current_version})")
                return

            logger.info(f"🔄 Обновление схемы БД: {current_version} -> {CURRENT_SCHEMA_VERSION}")
            if self.db_path.exists():
                backup_path = self.db_path.parent / f"backup_before_migration_v{CURRENT_SCHEMA_VERSION}.db"
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"💾 Создан бэкап: {backup_path}")

            for version in range(current_version + 1, CURRENT_SCHEMA_VERSION + 1):
                if version not in self._migrations:
                    raise RuntimeError(f"❌ Отсутствует миграция для версии {version}")
                logger.info(f"⏳ Применение миграции v{version}...")
                try:
                    self._migrations[version](cursor)
                    cursor.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (version,))
                    logger.info(f"✅ Миграция v{version} успешно применена")
                except Exception as e:
                    logger.critical(f"💥 Ошибка миграции v{version}: {e}")
                    raise RuntimeError(f"Миграция v{version} провалилась.") from e
            logger.info(f"🎉 Схема БД успешно обновлена до версии {CURRENT_SCHEMA_VERSION}")

    def _migration_v1_initial(self, cursor):
        cursor.execute("""CREATE TABLE parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category_id INTEGER,
            part_type TEXT, package TEXT, manufacturer TEXT, part_number TEXT,
            quantity INTEGER DEFAULT 0, price REAL DEFAULT 0, location TEXT,
            status TEXT DEFAULT 'new', image_path TEXT, datasheet_path TEXT, notes TEXT,
            revision_date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL)""")
        cursor.execute("CREATE INDEX idx_parts_name ON parts(name)")
        cursor.execute("CREATE INDEX idx_parts_category ON parts(category_id)")
        cursor.execute("CREATE INDEX idx_parts_status ON parts(status)")
        cursor.execute("CREATE INDEX idx_parts_location ON parts(location)")
        cursor.execute("""CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,
            parent_id INTEGER, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS dictionaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, value TEXT NOT NULL, UNIQUE(type, value))""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, description TEXT,
            status TEXT DEFAULT 'open', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS project_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, part_id INTEGER NOT NULL,
            quantity_needed INTEGER NOT NULL DEFAULT 1, quantity_reserved INTEGER DEFAULT 0, notes TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE, UNIQUE(project_id, part_id))""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS parts_archive (
            id INTEGER PRIMARY KEY, part_data TEXT NOT NULL,
            archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reason TEXT)""")
        cursor.execute("""INSERT OR IGNORE INTO dictionaries (type, value) VALUES 
            ('status', 'new'), ('status', 'used'), ('status', 'suspect'), ('status', 'broken')""")

    def _migration_v2_russian_statuses(self, cursor):
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("CREATE TABLE parts_backup AS SELECT * FROM parts")
        cursor.execute("DROP TABLE parts")
        cursor.execute("""CREATE TABLE parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category_id INTEGER,
            part_type TEXT, package TEXT, manufacturer TEXT, part_number TEXT,
            quantity INTEGER DEFAULT 0, price REAL DEFAULT 0, location TEXT,
            status TEXT DEFAULT 'Новое', image_path TEXT, datasheet_path TEXT, notes TEXT,
            revision_date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL)""")
        cursor.execute("INSERT INTO parts SELECT id, name, category_id, part_type, package, manufacturer, part_number, quantity, price, location, status, image_path, datasheet_path, notes, revision_date, created_at, updated_at FROM parts_backup")
        cursor.execute("DROP TABLE parts_backup")
        cursor.execute("UPDATE parts SET status = 'Новое' WHERE status = 'new'")
        cursor.execute("UPDATE parts SET status = 'Б/У проверено' WHERE status = 'used'")
        cursor.execute("UPDATE parts SET status = 'Б/У не проверено' WHERE status = 'suspect'")
        cursor.execute("UPDATE parts SET status = 'Неисправно' WHERE status = 'broken'")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_name ON parts(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_category ON parts(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_status ON parts(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_location ON parts(location)")
        cursor.execute("PRAGMA foreign_keys = ON")

    # ==================== КАТЕГОРИИ (НОВЫЕ МЕТОДЫ) ====================
    def get_category_part_count_recursive(self, cat_id: int) -> int:
        descendants = [cat_id]
        queue = [cat_id]
        with self.get_cursor() as cursor:
            while queue:
                current = queue.pop(0)
                cursor.execute("SELECT id FROM categories WHERE parent_id = ?", (current,))
                for child in cursor.fetchall():
                    cid = child[0]
                    descendants.append(cid)
                    queue.append(cid)
            placeholders = ','.join('?' for _ in descendants)
            cursor.execute(f"SELECT COALESCE(SUM(quantity), 0) FROM parts WHERE category_id IN ({placeholders})", descendants)
            return cursor.fetchone()[0]

    def get_category_children_count(self, cat_id: int) -> int:
        with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM categories WHERE parent_id = ?", (cat_id,))
            return cursor.fetchone()[0]

    def rename_category(self, cat_id: int, new_name: str):
        with self.get_cursor() as cursor:
            cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (new_name, cat_id))

    def delete_category(self, cat_id: int):
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))

    def move_category(self, cat_id: int, new_parent_id: Optional[int]):
        with self.get_cursor() as cursor:
            cursor.execute("UPDATE categories SET parent_id = ? WHERE id = ?", (new_parent_id, cat_id))

    # ==================== СТАНДАРТНЫЕ МЕТОДЫ ====================
    def get_all_parts_filtered(self, category_id=None, filter_type="all", location_path=None) -> List[Dict[str, Any]]:
        with self.get_cursor() as cursor:
            query = "SELECT id, name, part_type, package, quantity, price, location, status FROM parts WHERE 1=1"
            params = []
            if category_id is not None:
                query += " AND category_id = ?"
                params.append(category_id)
            if filter_type == "in_stock": query += " AND quantity > 0"
            elif filter_type == "low_stock": query += " AND quantity > 0 AND quantity < 10"
            elif filter_type == "out_of_stock": query += " AND (quantity = 0 OR status = 'Неисправно')"
            if location_path:
                query += " AND location LIKE ?"
                params.append(f"{location_path}%")
            query += " ORDER BY name"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_part(self, part_id: int) -> Optional[Dict[str, Any]]:
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM parts WHERE id = ?", (part_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_categories(self) -> List[tuple]:
        with self.get_cursor() as cursor:
            cursor.execute("SELECT id, name, parent_id FROM categories ORDER BY name")
            return cursor.fetchall()

    def get_dictionary_values(self, dict_type: str) -> List[str]:
        with self.get_cursor() as cursor:
            cursor.execute("SELECT value FROM dictionaries WHERE type = ?", (dict_type,))
            return [row[0] for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM parts")
            total_parts = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(quantity) FROM parts")
            total_quantity = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(quantity * price) FROM parts")
            total_value = cursor.fetchone()[0] or 0.0
            cursor.execute("SELECT COUNT(*) FROM parts WHERE quantity = 0")
            out_of_stock = cursor.fetchone()[0]
            return {'total_parts': total_parts, 'total_quantity': total_quantity, 'total_value': round(total_value, 2), 'out_of_stock': out_of_stock}

    def create_part(self, data: Dict[str, Any]) -> int:
        with self.get_cursor() as cursor:
            cursor.execute("""INSERT INTO parts (name, category_id, part_type, package, manufacturer, part_number, quantity, price, location, status, image_path, datasheet_path, notes, revision_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (data['name'], data.get('category_id'), data.get('part_type'), data.get('package'), data.get('manufacturer'), data.get('part_number'), data.get('quantity', 0), data.get('price', 0), data.get('location'), data.get('status', 'Новое'), data.get('image_path'), data.get('datasheet_path'), data.get('notes'), data.get('revision_date')))
            return cursor.lastrowid

    def create_category(self, name: str, parent_id=None, description="") -> int:
        with self.get_cursor() as cursor:
            cursor.execute("INSERT OR IGNORE INTO categories (name, parent_id, description) VALUES (?, ?, ?)", (name, parent_id, description))
            cursor.execute("SELECT id FROM categories WHERE name = ?", (name,))
            row = cursor.fetchone()
            return row[0] if row else None

    def update_part(self, part_id: int, data: Dict[str, Any]):
        with self.get_cursor() as cursor:
            cursor.execute("""UPDATE parts SET name=?, part_type=?, package=?, manufacturer=?, part_number=?, quantity=?, price=?, location=?, status=?, image_path=?, datasheet_path=?, notes=?, revision_date=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""", (data['name'], data.get('part_type'), data.get('package'), data.get('manufacturer'), data.get('part_number'), data.get('quantity', 0), data.get('price', 0), data.get('location'), data.get('status', 'Новое'), data.get('image_path'), data.get('datasheet_path'), data.get('notes'), data.get('revision_date'), part_id))

    def delete_part(self, part_id: int, reason: str = "deleted_by_user"):
        part = self.get_part(part_id)
        if part:
            with self.get_cursor() as cursor:
                cursor.execute("INSERT OR REPLACE INTO parts_archive (id, part_data, reason) VALUES (?, ?, ?)", (part_id, json.dumps(part, default=str), reason))
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM parts WHERE id = ?", (part_id,))

    def get_location_tree(self) -> dict:
        tree = {}
        with self.get_cursor() as cursor:
            cursor.execute("SELECT DISTINCT location FROM parts WHERE location IS NOT NULL AND length(trim(location)) > 0")
            for row in cursor.fetchall():
                loc = row[0].strip()
                if not loc: continue
                parts = [p.strip() for p in loc.split('/') if p.strip()]
                current_level = tree
                for part in parts:
                    if part not in current_level: current_level[part] = {}
                    current_level = current_level[part]
        return tree

    def backup(self, backup_path: Optional[Path] = None) -> Path:
        if backup_path is None: backup_path = Path(self.db_path).parent / f"backup_{Path(self.db_path).stem}.db"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.db_path, backup_path)
        return backup_path