# utils/exporter.py
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, Alignment

logger = logging.getLogger(__name__)

def export_to_csv(parts: List[Dict[str, Any]], file_path: Path) -> int:
    """Экспорт списка деталей в CSV (utf-8-sig, разделитель ;)."""
    if not parts:
        return 0
    fieldnames = [
        'id', 'name', 'category', 'part_type', 'value_numeric', 'value_unit',
        'package', 'diameter_mm', 'height_mm', 'lead_pitch_mm', 'lead_diameter_mm',
        'quantity', 'price', 'location', 'status', 'manufacturer', 'part_number',
        'revision_date', 'description', 'image_path', 'image_path_2', 'image_path_3', 'datasheet_path'
    ]
    for p in parts:
        if 'category_name' not in p:
            p['category_name'] = p.get('category', '')
        for k in fieldnames:
            if p.get(k) is None:
                p[k] = ''
    with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        for p in parts:
            writer.writerow({k: p.get(k, '') for k in fieldnames})
    return len(parts)

def export_to_excel(parts: List[Dict[str, Any]], file_path: Path) -> int:
    """Экспорт списка деталей в Excel (xlsx)."""
    if not parts:
        return 0
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "RadioPartsDB"

    headers = [
        'ID', 'Наименование', 'Категория', 'Тип детали', 'Номинал числовой', 'Единица',
        'Корпус', 'Диаметр (мм)', 'Высота (мм)', 'Шаг выводов (мм)', 'Толщина выводов (мм)',
        'Количество', 'Цена', 'Место хранения', 'Состояние', 'Производитель', 'Артикул',
        'Дата ревизии', 'Заметки', 'Изображение 1', 'Изображение 2', 'Изображение 3', 'Даташит'
    ]
    ws.append(headers)
    for col in range(1, len(headers)+1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    for p in parts:
        row = [
            p.get('id', ''),
            p.get('name', ''),
            p.get('category_name', p.get('category', '')),
            p.get('part_type', ''),
            p.get('value_numeric', ''),
            p.get('value_unit', ''),
            p.get('package', ''),
            p.get('diameter_mm', ''),
            p.get('height_mm', ''),
            p.get('lead_pitch_mm', ''),
            p.get('lead_diameter_mm', ''),
            p.get('quantity', 0),
            p.get('price', 0),
            p.get('location', ''),
            p.get('status', ''),
            p.get('manufacturer', ''),
            p.get('part_number', ''),
            p.get('revision_date', ''),
            p.get('notes', ''),
            p.get('image_path', ''),
            p.get('image_path_2', ''),
            p.get('image_path_3', ''),
            p.get('datasheet_path', ''),
        ]
        ws.append(row)

    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[col_letter].width = adjusted_width

    wb.save(file_path)
    return len(parts)