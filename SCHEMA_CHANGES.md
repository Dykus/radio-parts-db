# 🗄 Изменение структуры Базы Данных

## 📜 Правило
Любое изменение схемы (колонки, типы, индексы, данные) делается **только через систему миграций**.

## 🛠 Алгоритм (4 шага)
1. Откройте `core/database.py`
2. Увеличьте `CURRENT_SCHEMA_VERSION` на `+1`
3. В `__init__` добавьте строку: `self._migrations[НОМЕР] = self._migration_vНОМЕР_описание`
4. Создайте метод `_migration_vНОМЕР_описание(self, cursor):` и напишите SQL-логику внутри.

## 💡 Пример
Хочу добавить колонку `weight` в таблицу `parts`:
```python
CURRENT_SCHEMA_VERSION = 3  # было 2

# В __init__:
self._migrations[3] = self._migration_v3_add_weight

# Новый метод:
def _migration_v3_add_weight(self, cursor):
    cursor.execute("ALTER TABLE parts ADD COLUMN weight REAL DEFAULT 0.0")
    logger.info("✅ Добавлена колонка weight")