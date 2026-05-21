# import_db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/radioparts.db")
SQL_FILE = Path("import_categories.sql")

if not DB_PATH.exists():
    print(f"❌ База данных не найдена: {DB_PATH}")
    exit(1)

if not SQL_FILE.exists():
    print(f"❌ SQL-файл не найден: {SQL_FILE}")
    exit(1)

print(f"🔄 Импорт категорий из {SQL_FILE}...")

conn = sqlite3.connect(DB_PATH)
try:
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    print("✅ Категории успешно импортированы!")
    
    # Проверка
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM categories")
    count = cursor.fetchone()[0]
    print(f"📊 Всего категорий в базе: {count}")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    conn.rollback()
finally:
    conn.close()