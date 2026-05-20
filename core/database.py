import sqlite3
from pathlib import Path
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._connection = None

    def connect(self):
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
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
        with self.get_cursor() as c:
            c.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT UNIQUE, parent_id INTEGER, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            c.execute("CREATE TABLE IF NOT EXISTS dictionaries (id INTEGER PRIMARY KEY, type TEXT CHECK(type IN ('location','package','status')), value TEXT, UNIQUE(type, value))")
            c.execute("CREATE TABLE IF NOT EXISTS parts (id INTEGER PRIMARY KEY, name TEXT, category_id INTEGER, part_type TEXT, package TEXT, manufacturer TEXT, part_number TEXT, quantity INTEGER DEFAULT 0, price REAL DEFAULT 0, location TEXT, status TEXT DEFAULT 'new' CHECK(status IN ('new','used','suspect','broken')), image_path TEXT, datasheet_path TEXT, revision_date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (category_id) REFERENCES categories(id))")
            c.execute("CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT UNIQUE, description TEXT, status TEXT DEFAULT 'open' CHECK(status IN ('open','closed')), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            c.execute("CREATE TABLE IF NOT EXISTS project_parts (id INTEGER PRIMARY KEY, project_id INTEGER, part_id INTEGER, quantity_needed INTEGER DEFAULT 1, quantity_reserved INTEGER DEFAULT 0, notes TEXT, UNIQUE(project_id, part_id), FOREIGN KEY (project_id) REFERENCES projects(id), FOREIGN KEY (part_id) REFERENCES parts(id))")
            c.execute("CREATE TABLE IF NOT EXISTS parts_archive (id INTEGER PRIMARY KEY, part_data TEXT, archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reason TEXT)")
            c.execute("INSERT OR IGNORE INTO dictionaries (type, value) VALUES ('status','new'),('status','used'),('status','suspect'),('status','broken')")
        logger.info("Схема БД инициализирована")

    def backup(self, backup_path: Path):
        import shutil
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.db_path, backup_path)