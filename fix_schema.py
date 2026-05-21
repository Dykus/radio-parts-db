# fix_schema.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/radioparts.db")

print(f"🔧 Исправление схемы базы данных: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
# ⚠️ УДАЛИТ ВСЕ КАТЕГОРИИ И СБРОСИТ ID
cursor.execute("DELETE FROM parts WHERE category_id IS NOT NULL")
cursor.execute("DELETE FROM categories")
cursor.execute("DELETE FROM sqlite_sequence WHERE name='categories'")
conn.commit()
print("🧹 База очищена")
try:
    # 1. Создаём временную таблицу с правильной структурой
    print("📋 Создаём временную таблицу...")
    cursor.execute("""
        CREATE TABLE categories_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES categories_new(id) ON DELETE CASCADE,
            UNIQUE(name, parent_id)
        )
    """)
    
    # 2. Копируем данные (если есть)
    print("📦 Копируем существующие данные...")
    cursor.execute("""
        INSERT INTO categories_new (id, name, parent_id, description, created_at)
        SELECT id, name, parent_id, description, created_at FROM categories
    """)
    
    # 3. Удаляем старую таблицу и переименовываем новую
    print("🔄 Заменяем таблицу...")
    cursor.execute("DROP TABLE categories")
    cursor.execute("ALTER TABLE categories_new RENAME TO categories")
    
    # 4. Восстанавливаем индексы
    print("🔍 Восстанавливаем индексы...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id)")
    
    conn.commit()
    print("✅ Схема успешно обновлена!")
    print("✨ Теперь можно создавать категории с одинаковыми именами в разных ветках")
    
    # Проверка
    cursor.execute("SELECT COUNT(*) FROM categories")
    count = cursor.fetchone()[0]
    print(f"📊 Всего категорий в базе: {count}")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    conn.rollback()
    print("💡 Совет: закройте программу перед запуском миграции")
finally:
    conn.close()