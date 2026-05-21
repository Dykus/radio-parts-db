# utils/importer.py
import csv
import logging
import re
import io
from core.database import Database

logger = logging.getLogger(__name__)

def guess_encoding(file_path):
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
    if not text:
        return ""
    clean = re.compile('<.*?>')
    return clean.sub('', text).strip()

def parse_date(date_str):
    if not date_str:
        return None
    try:
        d, m, y = date_str.strip().split('.')
        return f"{y}-{m}-{d}"
    except Exception:
        return None

def map_status(status_str):
    """Сопоставляет русские/английские статусы с новыми русскими состояниями."""
    if not status_str:
        return 'Новое'
    s = status_str.strip().lower()
    
    if s in ['новое', 'new', 'ок', 'исправное', 'отличное', 'excellent']:
        return 'Новое'
    if s in ['хорошее', 'good']:
        return 'Хорошее'
    if s.startswith('б/у') or s.startswith('used'):
        if 'провер' in s or 'checked' in s:
            return 'Б/У проверено'
        return 'Б/У не проверено'
    if s in ['плохое', 'bad', 'suspect']:
        return 'Плохое'
    if s in ['неисправно', 'defective', 'сломано', 'broken', 'нет']:
        return 'Неисправно'
    return 'Б/У не проверено'

def import_csv(db: Database, file_path: str) -> tuple:
    encoding = guess_encoding(file_path)
    logger.info(f"Определена кодировка: {encoding}")

    imported_count = 0
    error_count = 0
    skipped_count = 0

    try:
        with open(file_path, 'r', encoding=encoding, newline='') as f:
            first_line = f.readline()
            delimiter = ';' if ';' in first_line else ','
            
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
            
            lines = f.readlines()
            fixed_header = delimiter.join([f'"{h}"' for h in unique_headers]) + "\n"
            csv_data = io.StringIO(fixed_header + "".join(lines))
            
            reader = csv.DictReader(csv_data, delimiter=delimiter)
            logger.info(f"Обработано колонок: {len(reader.fieldnames)}")

            def get_val(key, default=''):
                val = row.get(key, default)
                return val.strip().strip('"') if val else default

            for i, row in enumerate(reader, start=2):
                try:
                    radio = get_val('Радиоэлемент')
                    p_type = get_val('Тип')
                    
                    val1 = get_val('Значение')
                    unit1 = get_val('Единица измерения')
                    val2 = get_val('Значение_1')
                    unit2 = get_val('Единица измерения_1')
                    
                    params = []
                    if val1: params.append(f"{val1} {unit1}".strip())
                    if val2: params.append(f"{val2} {unit2}".strip())
                    full_val = " ".join(params).strip()
                    
                    name = " ".join(filter(None, [radio, p_type, full_val])).strip()
                    if not name:
                        skipped_count += 1
                        continue

                    category = radio if radio else p_type
                    package = get_val('Корпус')
                    manufacturer = get_val('Производитель')
                    
                    price_raw = get_val('Цена за шт.')
                    price = float(price_raw.replace(',', '.').replace('₽', '').replace('$', '').strip()) if price_raw else 0.0
                    
                    status = map_status(get_val('Состояние'))
                    
                    place = get_val('Место')
                    container = get_val('Контейнер')
                    cell = get_val('Ячейка')
                    
                    location_parts = [p for p in [place, container, cell] if p]
                    location = ' / '.join(location_parts) if location_parts else ''
                    
                    qty_raw = get_val('Количество')
                    quantity = int(float(qty_raw.replace(',', '.'))) if qty_raw else 0
                    
                    revision_date = parse_date(get_val('Время ревизии'))
                    
                    desc_html = get_val('Описание')
                    notes = clean_html(desc_html)
                    
                    specs = get_val('диаметр × высота')
                    if specs:
                        notes += f"\nРазмеры: {specs}" if notes else f"Размеры: {specs}"
                    
                    datasheet = get_val('Ссылка на даташит') or get_val('Datasheed') or get_val('Ссылка в сеть')
                    image = get_val('Внешний вид') or get_val('По фото')
                    
                    part_data = {
                        'name': name,
                        'category': category,
                        'part_type': p_type,
                        'package': package,
                        'manufacturer': manufacturer,
                        'quantity': quantity,
                        'price': price,
                        'location': location,
                        'status': status,
                        'revision_date': revision_date,
                        'notes': notes,
                        'image_path': image,
                        'datasheet_path': datasheet
                    }
                    
                    cat_id = None
                    if category:
                        cats = db.get_categories()
                        cat_id = next((c[0] for c in cats if c[1] == category), None)
                        if cat_id is None:
                            cat_id = db.create_category(category)
                        part_data['category_id'] = cat_id
                    
                    db.create_part(part_data)
                    imported_count += 1
                    
                    if imported_count <= 5:
                        logger.info(f"✅ Строка {i}: добавлен '{name}' -> {location}")

                except Exception as e:
                    logger.error(f"❌ Ошибка в строке {i}: {e}")
                    error_count += 1

    except Exception as e:
        logger.error(f"Критическая ошибка чтения файла: {e}")
        return 0, 1

    logger.info(f"Импорт завершен: добавлено {imported_count}, пропущено {skipped_count}, ошибок {error_count}")
    return imported_count, error_count