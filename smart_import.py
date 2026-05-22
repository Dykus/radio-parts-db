# smart_import.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/radioparts.db")

CATEGORIES = {
    "Arduino": ["Модуль", "Плата"],
    "СИС": ["Направляющая", "Подшипник", "Ремень"],
    "DC - DC": ["Повышающий", "Понижающий"],
    "Акустика": ["Микрофон"],
    "Датчик": ["Температуры"],
    "Диод": ["Быстродействующий", "Варикап", "Выпрямительный", "Высоковольтный", "Диодная сборка", "Мост", "Силовой", "Стабилитрон", "Шоттки"],
    "Индуктивность": ["0307 0.25W", "0510 1W"],
    "Кнопки, переключатели": ["Внешний", "Для корпуса", "Для плат", "Тактовая кнопка"],
    "Компьютер": ["Оперативная память"],
    "Конденсатор": ["SMD", "Керамический", "Дисковый", "Пленочный", "Полипропиленовый", "Электролитический", "Суперконденсатор"],
    "Микросхемы": ["AVR", "Отечественные", "Панелька", "Сборка Дарлингтона", "УНЧ"],
    "Оптоэлектроника": ["Индикаторы и дисплеи", "Лампа", "Оптопара", "Светодиод", "ИК"],
    "Предохранитель": ["Держатель для корпуса", "Держатель для платы", "Стекло 5x20"],
    "Радиолампы": ["Газоразрядный индикатор"],
    "Разъем": ["Внешний", "Для корпуса", "Для плат", "Клеммник"],
    "Резистор": ["SMD", "Выводной", "Переменный", "Подстроечный"],
    "Резонаторы и фильтры": ["Кварцевый резонатор"],
    "Реле": [],
    "Симистор": ["Импортный", "Отечественный"],
    "Тиристор": ["Импортный", "Отечественный"],
    "Транзистор": ["Зарубежный", "Отечественный"],
}

SUBCATEGORIES = {
    "Направляющая": ["Вал 10 мм", "Вал 16 мм"],
    "Подшипник": ["Линейный", "Обычный", "Опорный"],
    "Микрофон": ["Электретный"],
    "Температуры": ["Термистор"],
    "Оперативная память": ["DDR1", "DDR2", "DDR3", "DDR4"],
    "SMD": ["0805", "1206"],
    "Керамический": ["NPO", "Высоковольтный"],
    "Дисковый": ["3мм", "5мм", "Квадратный"],
    "Пленочный": ["200V", "250V", "400V", "630V", "Высоковольтный"],
    "Полипропиленовый": ["250V", "275V", "310V"],
    "Электролитический": ["100V", "10V", "160V", "16V", "200V", "250V", "25V", "280V", "350V", "35V", "400V", "450V", "50V", "5kV", "6.3V", "63V"],
    "AVR": ["EEPROM", "Микроконтроллер"],
    "Индикаторы и дисплеи": ["LCD", "LED"],
    "LED": ["7 сегментный 1 разряд", "7 сегментный 2 разряда", "7 сегментный 4 разряда"],
    "Светодиод": ["10 мм", "3 мм", "5 мм", "RGB", "SMD", "Мощный"],
    "Клеммник": ["Для плат"],
    "Выводной": ["0.125 W", "0.25 W", "0.5 W", "1 W", "2 W", "5 W", "7 W"],
    "Зарубежный": ["MOSFET N - канал", "MOSFET P - канал", "NPN"],
    "Отечественный": ["MOSFET N - канал", "MOSFET P - канал", "NPN", "PNP"],
    "NPN": ["Высокочастотный", "Мощный", "Обычный"],
    "PNP": ["Высокочастотный", "Обычный"],
    "Высоковольтный": ["1.6kV", "3kV", "5kV", "6.3kV"],
    "Мощный": ["1W", "3W"],
}

def get_or_create_category(cursor, name, parent_id=None):
    if parent_id is None:
        cursor.execute("SELECT id FROM categories WHERE name = ? AND parent_id IS NULL", (name,))
    else:
        cursor.execute("SELECT id FROM categories WHERE name = ? AND parent_id = ?", (name, parent_id))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO categories (name, parent_id) VALUES (?, ?)", (name, parent_id))
    return cursor.lastrowid

def import_categories():
    if not DB_PATH.exists():
        print(f"❌ База данных не найдена: {DB_PATH}")
        return
    print(f"🔄 Импорт категорий в {DB_PATH}...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        for root_name, children in CATEGORIES.items():
            root_id = get_or_create_category(cursor, root_name, None)
            for child_name in children:
                child_id = get_or_create_category(cursor, child_name, root_id)
                if child_name in SUBCATEGORIES:
                    for subchild_name in SUBCATEGORIES[child_name]:
                        get_or_create_category(cursor, subchild_name, child_id)
        
        conn.commit()
        print("✅ Категории успешно импортированы!")
        
        cursor.execute("SELECT COUNT(*) FROM categories")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM categories WHERE parent_id IS NULL")
        roots = cursor.fetchone()[0]
        
        print(f"📊 Всего категорий: {total}")
        print(f"📁 Корневых категорий: {roots}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    import_categories()