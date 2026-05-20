# core/database.py
"""
Модуль работы с базой данных SQLite.
Инициализация схем, подключения, базовые операции CRUD.
"""
import sqlite3
import json
import shutil
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class Database:
    """Управление подключением и схемой БД."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._connection = None
    
    def connect(self):
        """Установить подключение к БД."""
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False  # Для PyQt: доступ из разных потоков
            )
            self._connection.row_factory = sqlite3.Row  # Доступ к полям по имени
            logger.info(f"Подключено к БД: {self.db_path}")
        return self._connection
    
    def close(self):
        """Закрыть подключение."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Отключено от БД")
    
    @contextmanager
    def get_cursor(self):
        """Контекстный менеджер для безопасной работы с курсором."""
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
        """Создать таблицы, если их нет."""
        with self.get_cursor() as cursor:
            # Таблица категорий (иерархическая)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    parent_id INTEGER,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE
                )
            """)
            
            # Таблица справочников: места хранения, корпуса, статусы
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dictionaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL CHECK(type IN ('location', 'package', 'status')),
                    value TEXT NOT NULL,
                    UNIQUE(type, value)
                )
            """)
            
            # Основная таблица компонентов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category_id INTEGER,
                    
                    -- Технические параметры
                    part_type TEXT,
                    package TEXT,
                    manufacturer TEXT,
                    part_number TEXT,
                    
                    -- Учёт
                    quantity INTEGER DEFAULT 0,
                    price REAL DEFAULT 0,
                    location TEXT,
                    status TEXT DEFAULT 'new' CHECK(status IN ('new', 'used', 'suspect', 'broken')),
                    
                    -- Медиа
                    image_path TEXT,
                    datasheet_path TEXT,
                    
                    -- Временные метки
                    revision_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
                )
            """)
            
            # Индексы для ускорения поиска
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_name ON parts(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_category ON parts(category_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_status ON parts(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_location ON parts(location)")
            
            # Таблица проектов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    status TEXT DEFAULT 'open' CHECK(status IN ('open', 'closed')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица связи проектов и компонентов (резервирование)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_parts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    part_id INTEGER NOT NULL,
                    quantity_needed INTEGER NOT NULL DEFAULT 1,
                    quantity_reserved INTEGER DEFAULT 0,
                    notes TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE,
                    UNIQUE(project_id, part_id)
                )
            """)
            
            # Таблица архива (для функции "архив по номеру")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parts_archive (
                    id INTEGER PRIMARY KEY,
                    part_data TEXT NOT NULL,
                    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT
                )
            """)
            
            # Заполним справочник статусов по умолчанию
            cursor.execute("""
                INSERT OR IGNORE INTO dictionaries (type, value) VALUES 
                ('status', 'new'),
                ('status', 'used'),
                ('status', 'suspect'),
                ('status', 'broken')
            """)
            
        logger.info("Схема БД инициализирована")
    
    # ==================== ЧТЕНИЕ ====================
    
    def get_part(self, part_id: int) -> Optional[Dict[str, Any]]:
        """Получить компонент по ID."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM parts WHERE id = ?", (part_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_parts(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получить все компоненты (опционально фильтруя по категории)."""
        with self.get_cursor() as cursor:
            if category_id:
                cursor.execute("""
                    SELECT id, name, part_type, package, quantity, price, location, status 
                    FROM parts WHERE category_id = ? ORDER BY name
                """, (category_id,))
            else:
                cursor.execute("""
                    SELECT id, name, part_type, package, quantity, price, location, status 
                    FROM parts ORDER BY name
                """)
            return [dict(row) for row in cursor.fetchall()]
    
    def search_parts(self, query: str) -> List[Dict[str, Any]]:
        """Поиск компонентов по названию, типу или артикулу."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, part_type, package, quantity, price, location, status 
                FROM parts 
                WHERE name LIKE ? OR part_type LIKE ? OR part_number LIKE ? OR manufacturer LIKE ?
                ORDER BY name
            """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_categories(self) -> List[tuple]:
        """Получить все категории: [(id, name, parent_id), ...]"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT id, name, parent_id FROM categories ORDER BY name")
            return cursor.fetchall()
    
    def get_dictionary_values(self, dict_type: str) -> List[str]:
        """Получить значения справочника по типу (location, package, status)."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT value FROM dictionaries WHERE type = ?", (dict_type,))
            return [row[0] for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить сводную статистику по складу."""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM parts")
            total_parts = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(quantity) FROM parts")
            total_quantity = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT SUM(quantity * price) FROM parts")
            total_value = cursor.fetchone()[0] or 0.0
            
            cursor.execute("SELECT COUNT(*) FROM parts WHERE quantity = 0")
            out_of_stock = cursor.fetchone()[0]
            
            return {
                'total_parts': total_parts,
                'total_quantity': total_quantity,
                'total_value': round(total_value, 2),
                'out_of_stock': out_of_stock
            }
    
    # ==================== СОЗДАНИЕ ====================
    
    def create_part(self, data: Dict[str, Any]) -> int:
        """Создать новый компонент, вернуть его ID."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO parts (
                    name, category_id, part_type, package, manufacturer,
                    part_number, quantity, price, location, status,
                    image_path, datasheet_path, revision_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['name'],
                data.get('category_id'),
                data.get('part_type'),
                data.get('package'),
                data.get('manufacturer'),
                data.get('part_number'),
                data.get('quantity', 0),
                data.get('price', 0),
                data.get('location'),
                data.get('status', 'new'),
                data.get('image_path'),
                data.get('datasheet_path'),
                data.get('revision_date')
            ))
            return cursor.lastrowid
    
    def create_category(self, name: str, parent_id: Optional[int] = None, description: str = "") -> int:
        """Создать новую категорию, вернуть её ID."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name, parent_id, description) VALUES (?, ?, ?)",
                (name, parent_id, description)
            )
            return cursor.lastrowid
    
    def add_dictionary_value(self, dict_type: str, value: str):
        """Добавить значение в справочник."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT OR IGNORE INTO dictionaries (type, value) VALUES (?, ?)",
                (dict_type, value)
            )
    
    # ==================== ОБНОВЛЕНИЕ ====================
    
    def update_part(self, part_id: int, data: Dict[str, Any]):
        """Обновить данные компонента."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE parts SET 
                    name = ?, part_type = ?, package = ?, manufacturer = ?, 
                    part_number = ?, quantity = ?, price = ?, location = ?, 
                    status = ?, image_path = ?, datasheet_path = ?, 
                    revision_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data['name'],
                data.get('part_type'),
                data.get('package'),
                data.get('manufacturer'),
                data.get('part_number'),
                data.get('quantity', 0),
                data.get('price', 0),
                data.get('location'),
                data.get('status', 'new'),
                data.get('image_path'),
                data.get('datasheet_path'),
                data.get('revision_date'),
                part_id
            ))
    
    # ==================== УДАЛЕНИЕ ====================
    
    def delete_part(self, part_id: int, reason: str = "deleted_by_user"):
        """
        Удалить компонент с архивацией.
        Сначала сохраняет полные данные в parts_archive, затем удаляет из parts.
        """
        # 1. Получаем данные компонента
        part = self.get_part(part_id)
        if not part:
            return False
        
        # 2. Сохраняем в архив (с сохранением оригинального ID)
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT OR REPLACE INTO parts_archive (id, part_data, reason) VALUES (?, ?, ?)",
                (part_id, json.dumps(part, default=str), reason)
            )
        
        # 3. Удаляем из основной таблицы
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM parts WHERE id = ?", (part_id,))
        
        logger.info(f"Компонент #{part_id} удалён и перемещён в архив")
        return True
    
    def delete_category(self, category_id: int):
        """Удалить категорию (компоненты останутся, но без привязки)."""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    
    # ==================== ПРОЕКТЫ ====================
    
    def create_project(self, name: str, description: str = "") -> int:
        """Создать новый проект."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO projects (name, description) VALUES (?, ?)",
                (name, description)
            )
            return cursor.lastrowid
    
    def add_part_to_project(self, project_id: int, part_id: int, quantity: int, notes: str = ""):
        """Добавить компонент в проект (резервирование)."""
        with self.get_cursor() as cursor:
            # Проверяем, есть ли уже эта запись
            cursor.execute(
                "SELECT id FROM project_parts WHERE project_id = ? AND part_id = ?",
                (project_id, part_id)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Обновляем количество
                cursor.execute("""
                    UPDATE project_parts 
                    SET quantity_needed = quantity_needed + ?, notes = ?
                    WHERE project_id = ? AND part_id = ?
                """, (quantity, notes, project_id, part_id))
            else:
                # Создаём новую запись
                cursor.execute("""
                    INSERT INTO project_parts (project_id, part_id, quantity_needed, notes)
                    VALUES (?, ?, ?, ?)
                """, (project_id, part_id, quantity, notes))
    
    def get_project_parts(self, project_id: int) -> List[Dict[str, Any]]:
        """Получить все компоненты проекта с данными из основной таблицы."""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT pp.*, p.name, p.part_type, p.package, p.quantity as available_qty
                FROM project_parts pp
                JOIN parts p ON pp.part_id = p.id
                WHERE pp.project_id = ?
            """, (project_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== УТИЛИТЫ ====================
    
    def backup(self, backup_path: Optional[Path] = None) -> Path:
        """Создать резервную копию БД. Вернуть путь к бэкапу."""
        if backup_path is None:
            timestamp = Path(self.db_path).stem + "_backup_" + Path(self.db_path).suffix
            backup_path = Path(self.db_path).parent / timestamp
        
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Бэкап создан: {backup_path}")
        return backup_path
    
    def rotate_backups(self, backup_pattern: str, keep_count: int):
        """Удалить старые бэкапы, оставить только keep_count последних."""
        backups = sorted(
            Path(self.db_path).parent.glob(backup_pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        for old_backup in backups[keep_count:]:
            old_backup.unlink()
            logger.info(f"Удалён старый бэкап: {old_backup}")
    
    def vacuum(self):
        """Оптимизировать базу данных (освободить место)."""
        with self.get_cursor() as cursor:
            cursor.execute("VACUUM")
        logger.info("База данных оптимизирована (VACUUM)")