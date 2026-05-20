# utils/importer.py
import csv
import logging
import re
import io
from core.database import Database

logger = logging.getLogger(__name__)

def guess_encoding(file_path):
    """Определяет кодировку файла перебором."""
    encodings = ['utf-8-sig', 'utf-8', 'cp1251', 'latin1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read(1024)
            return enc
        except UnicodeDecodeError:
            continue
    return 'utf-8'

def clean_html(text):
    """Удаляет HTML-теги, оставляя чистый текст."""
    if not text:
        return ""
    clean = re.compile('<.*?>')
    return clean.sub('', text).strip()

def parse_date(date_str):
    """Преобразует DD.MM.YYYY в YYYY-MM-DD для SQLite."""
    if not date_str:
        return None
    try:
        d, m, y = date_str.strip().split('.')
        return f"{y}-{m}-{d}"
    except Exception:
        return None

def map_status(status_str):
    """Сопоставляет русские статусы Memento с БД."""
    if not status_str:
        return 'new'
    s = status_str.strip().lower()
    if s in ['новое', 'new', 'ок', 'исправное']:
        return 'new'
    if s.startswith('б/у') or s.startswith('used'):
        return 'used'
    if s in ['нет', 'bad', 'плохое', 'broken', 'сломано']:
        return 'broken'
    return 'suspect'

def import_csv(db: Database, file_path: str) -> tuple:
    """
    Импорт CSV из Memento Database.
    Специально настроен на структуру: Место -> Контейнер -> Ячейка.
    """
    encoding = guess_encoding(file_path)
    logger.info(f"Определена кодировка: {encoding}")

    imported_count = 0
    error_count = 0
    skipped_count = 0

    try:
        with open(file_path, 'r', encoding=encoding, newline='') as f:
            # Читаем первую строку для определения разделителя и заголовков
            first_line = f.readline()
            delimiter = ';' if ';' in first_line else ','
            
            # Исправляем дублирующиеся заголовки (Memento часто их дублирует)
            raw_headers = [h.strip().strip('"') for h in csv.reader([first_line], delimiter=delimiter).__next__()]
            unique_headers = []
            seen = {}
            for h in raw_headers:
                if h in seen:
                    seen[h] += 1
                    unique_headers.append(f"{h}_{seen[h]}")
                else:
                    seen[h] = 0
                    unique_headers.append(h)
            
            # Собираем файл обратно в память с исправленным заголовком
            lines = f.readlines()
            fixed_header = delimiter.join([f'"{h}"' for h in unique_headers]) + "\n"
            csv_data = io.StringIO(fixed_header + "".join(lines))
            
            reader = csv.DictReader(csv_data, delimiter=delimiter)
            logger.info(f"Обработано колонок: {len(reader.fieldnames)}")

            # Функция безопасного получения данных из строки
            def get_val(key, default=''):
                val = row.get(key, default)
                return val.strip().strip('"') if val else default

            for i, row in enumerate(reader, start=2):
                try:
                    # 1. Формируем полное имя: Радиоэлемент + Тип + Значение + Ед.изм
                    radio = get_val('Радиоэлемент')
                    p_type = get_val('Тип')
                    
                    # Собираем все пары Значение/Ед.изм (их может быть 1 или 2)
                    values = [get_val(k) for k in row if 'Значение' in k and get_val(k)]
                    units = [get_val(k) for k in row if 'Единица измерения' in k and get_val(k)]
                    full_val = " ".join([f"{v} {u}" for v, u in zip(values, units)]).strip()
                    
                    name = " ".join(filter(None, [radio, p_type, full_val])).strip()
                    if not name:
                        skipped_count += 1
                        continue

                    # 2. Основные поля
                    category = radio if radio else p_type
                    package = get_val('Корпус')
                    manufacturer = get_val('Производитель')
                    
                    price_raw = get_val('Цена за шт.')
                    price = float(price_raw.replace(',', '.').replace('₽', '').replace('$', '').strip()) if price_raw else 0.0
                    
                    status = map_status(get_val('Состояние'))
                    
                    # 3. Собираем ТРЕХУРОВНЕВОЕ место хранения
                    # Это критически важно для работы навигатора!
                    # Берем колонки: Место, Контейнер, Ячейка
                    place = get_val('Место')
                    container = get_val('Контейнер')
                    cell = get_val('Ячейка')
                    
                    # Склеиваем их через ' / '
                    location_parts = [p for p in [place, container, cell] if p]
                    location = ' / '.join(location_parts) if location_parts else ''
                    
                    qty_raw = get_val('Количество')
                    quantity = int(float(qty_raw.replace(',', '.'))) if qty_raw else 0
                    
                    revision_date = parse_date(get_val('Время ревизии'))
                    
                    # 4. Описание и заметки (чистим HTML)
                    desc_html = get_val('Описание')
                    notes = clean_html(desc_html)
                    
                    specs = get_val('диаметр × высота')
                    if specs:
                        notes += f"\nРазмеры: {specs}" if notes else f"Размеры: {specs}"
                    
                    # 5. Ссылки и пути
                    datasheet = get_val('Ссылка на даташит') or get_val('Datasheed') or get_val('Ссылка в сеть')
                    image = get_val('Внешний вид') or get_val('По фото')
                    
                    # 6. Подготовка данных для БД
                    part_data = {
                        'name': name,
                        'category': category,
                        'part_type': p_type,
                        'package': package,
                        'manufacturer': manufacturer,
                        'quantity': quantity,
                        'price': price,
                        'location': location, # Сохраняем строку вида "Дом / Подвал / Ячейка"
                        'status': status,
                        'revision_date': revision_date,
                        'notes': notes,
                        'image_path': image,
                        'datasheet_path': datasheet
                    }
                    
                    # 7. Обработка категории (авто-создание если нет)
                    cat_id = None
                    if category:
                        cats = db.get_categories()
                        cat_id = next((c[0] for c in cats if c[1] == category), None)
                        if cat_id is None:
                            cat_id = db.create_category(category)
                        part_data['category_id'] = cat_id
                    
                    # 8. Сохранение в БД
                    db.create_part(part_data)
                    imported_count += 1
                    
                    if imported_count <= 3:
                        logger.info(f"✅ Строка {i}: добавлен '{name}' -> {location}")

                except Exception as e:
                    logger.error(f"❌ Ошибка в строке {i}: {e}")
                    error_count += 1

    except Exception as e:
        logger.error(f"Критическая ошибка чтения файла: {e}")
        return 0, 1

    logger.info(f"Импорт завершен: добавлено {imported_count}, пропущено {skipped_count}, ошибок {error_count}")
    return imported_count, error_count