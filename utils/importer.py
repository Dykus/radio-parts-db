# utils/importer.py
import csv
import logging
from core.database import Database

logger = logging.getLogger(__name__)

COLUMN_MAPPING = {
    'name': ['name', 'наименование', 'название', 'component', 'деталь'],
    'category': ['category', 'категория', 'группа', 'type'],
    'part_type': ['type', 'тип', 'part type', 'вид'],
    'package': ['package', 'корпус', 'case', 'footprint'],
    'manufacturer': ['manufacturer', 'производитель', 'vendor', 'mfg'],
    'part_number': ['part_number', 'артикул', 'mpn', 'p/n', 'part number'],
    'quantity': ['quantity', 'количество', 'qty', 'кол-во', 'count'],
    'price': ['price', 'цена', 'cost'],
    'location': ['location', 'место', 'storage', 'where'],
    'status': ['status', 'статус', 'состояние'],
    'image_path': ['image', 'изображение', 'photo', 'картинка'],
    'datasheet_path': ['datasheet', 'даташит', 'pdf', 'документ'],
    'notes': ['notes', 'заметки', 'comment', 'описание'],
}

def guess_encoding(file_path):
    """Попытка определить кодировку файла."""
    encodings = ['utf-8-sig', 'utf-8', 'cp1251', 'latin1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read(1024)
            return enc
        except UnicodeDecodeError:
            continue
    return 'utf-8'

def import_csv(db: Database, file_path: str) -> tuple:
    """Импорт CSV файла в БД."""
    encoding = guess_encoding(file_path)
    logger.info(f"Кодировка файла: {encoding}")
    
    imported_count = 0
    error_count = 0
    skipped_count = 0
    
    try:
        with open(file_path, 'r', encoding=encoding, newline='') as f:
            first_line = f.readline()
            f.seek(0)
            
            if ';' in first_line:
                delimiter = ';'
            elif ',' in first_line:
                delimiter = ','
            elif '\t' in first_line:
                delimiter = '\t'
            else:
                delimiter = ','
            
            logger.info(f"Разделитель: '{delimiter}'")
            logger.info(f"Первая строка: {first_line.strip()}")
            
            reader = csv.DictReader(f, delimiter=delimiter)
            logger.info(f"Заголовки CSV: {reader.fieldnames}")

            if not reader.fieldnames:
                logger.error("Пустой CSV файл или неверная кодировка")
                return 0, 1

            headers_map = {k.strip().lower(): k for k in reader.fieldnames}
            logger.info(f"Headers map: {headers_map}")
            
            db_to_csv_map = {}
            for db_field, possible_names in COLUMN_MAPPING.items():
                for name in possible_names:
                    if name.lower() in headers_map:
                        db_to_csv_map[db_field] = headers_map[name.lower()]
                        logger.info(f"  {db_field} -> {headers_map[name.lower()]}")
                        break
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    if row_num == 2:
                        logger.info(f"Пример строки данных: {row}")
                    
                    part_data = {}
                    
                    if 'name' in db_to_csv_map:
                        raw_name = row.get(db_to_csv_map['name'], '').strip()
                        if not raw_name:
                            skipped_count += 1
                            continue
                        part_data['name'] = raw_name
                    else:
                        first_col = reader.fieldnames[0]
                        raw_name = row.get(first_col, '').strip()
                        if not raw_name:
                            skipped_count += 1
                            continue
                        part_data['name'] = raw_name

                    for db_field, csv_header in db_to_csv_map.items():
                        if db_field == 'name': continue
                        val = row.get(csv_header, '').strip()
                        
                        if val:
                            if db_field == 'quantity':
                                try: part_data[db_field] = int(float(val.replace(',', '.')))
                                except: part_data[db_field] = 0
                            elif db_field == 'price':
                                try: part_data[db_field] = float(val.replace(',', '.'))
                                except: part_data[db_field] = 0.0
                            else:
                                part_data[db_field] = val
                    
                    if 'category' in part_data and part_data['category']:
                        cat_name = part_data.pop('category')
                        cats = db.get_categories()
                        cat_id = next((c[0] for c in cats if c[1] == cat_name), None)
                        if cat_id is None:
                            cat_id = db.create_category(cat_name)
                        part_data['category_id'] = cat_id

                    db.create_part(part_data)
                    imported_count += 1
                    logger.info(f"✅ Строка {row_num}: добавлен '{part_data['name']}'")

                except Exception as e:
                    logger.error(f"❌ Ошибка в строке {row_num}: {e}")
                    error_count += 1

    except Exception as e:
        logger.error(f"Ошибка чтения файла: {e}")
        return 0, 1

    logger.info(f"Итого: добавлено {imported_count}, пропущено {skipped_count}, ошибок {error_count}")
    return imported_count, error_count