# ui/dialogs/part_dialog.py
import re
import logging
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QDateTimeEdit, QTextEdit, QDialogButtonBox, QMessageBox, QFileDialog,
    QWidget, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt, QDate
from ui.dialogs.category_selector import CategorySelectorDialog

logger = logging.getLogger(__name__)

class PartDialog(QDialog):
    def __init__(self, parent=None, part_data=None, db=None, start_depth=0):
        super().__init__(parent)
        self.db = db
        self.part_data = part_data
        self.start_depth = start_depth
        self.setWindowTitle("✏️ Редактирование компонента")
        self.setMinimumWidth(650)
        self._init_ui()
        if part_data:
            self._fill_form(part_data)

    def _init_ui(self):
        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # --- Наименование ---
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Можно ввести вручную или нажать «Собрать название»")
        layout.addRow("Наименование *", self.name_edit)

        # --- Категория ---
        category_widget = QWidget()
        category_layout = QHBoxLayout(category_widget)
        category_layout.setContentsMargins(0, 0, 0, 0)
        category_layout.setSpacing(5)
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Выберите категорию")
        self.category_edit.setReadOnly(True)
        self.btn_select_category = QPushButton("📂 ...")
        self.btn_select_category.setMaximumWidth(40)
        self.btn_select_category.setToolTip("Выбрать категорию из дерева")
        self.btn_select_category.clicked.connect(self._open_category_selector)
        category_layout.addWidget(self.category_edit)
        category_layout.addWidget(self.btn_select_category)
        layout.addRow("Категория", category_widget)

        # --- Тип детали ---
        self.part_type_edit = QLineEdit()
        self.part_type_edit.setPlaceholderText("Например: Резистор, Конденсатор, Транзистор...")
        layout.addRow("Тип детали", self.part_type_edit)

        # --- Номинал / значение ---
        nominal_widget = QWidget()
        nominal_layout = QHBoxLayout(nominal_widget)
        nominal_layout.setContentsMargins(0, 0, 0, 0)
        nominal_layout.setSpacing(5)
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Введите номинал, например: 10, 2.2, 100")
        self.value_edit.textChanged.connect(self._on_value_text_changed)
        self.unit_combo = QComboBox()
        self.unit_combo.setEditable(False)
        self.unit_combo.setMinimumWidth(80)
        self.unit_combo.addItems(["", "Ом", "кОм", "МОм", "нФ", "мкФ", "пФ", "Ф", "Гн", "мГн", "мкГн", "В", "А", "мА"])
        nominal_layout.addWidget(self.value_edit)
        nominal_layout.addWidget(self.unit_combo)
        layout.addRow("Номинал / значение", nominal_widget)

        # --- Кнопка "Собрать название" ---
        self.btn_assemble = QPushButton("🧩 Собрать название")
        self.btn_assemble.setToolTip("Сформировать название из категории, номинала и корпуса")
        self.btn_assemble.clicked.connect(self._assemble_name)
        layout.addRow("", self.btn_assemble)

        # --- Корпус с подсказкой ---
        self.package_combo = QComboBox()
        self.package_combo.setEditable(True)
        self.package_combo.addItems(["", "0402", "0603", "0805", "1206", "SOT-23", "SOIC-8", "DIP-8", "TQFP-48", "TO-92", "TO-220"])
        self.package_combo.setPlaceholderText("Для конденсаторов: Диаметр x Высота, например 10x17")
        layout.addRow("Корпус", self.package_combo)

        # --- Состояние ---
        self.status_combo = QComboBox()
        self.status_combo.setEditable(False)
        self.status_combo.addItems([
            "🛒 Новое", "ℹ️ Б/У проверено", "❓ Б/У не проверено",
            "✅ Отличное", "✔️ Хорошее", "🚫 Плохое", "❌ Неисправно"
        ])
        self.status_combo.setCurrentText("🛒 Новое")
        layout.addRow("Состояние", self.status_combo)

        # --- Производитель ---
        self.manufacturer_edit = QLineEdit()
        layout.addRow("Производитель", self.manufacturer_edit)

        # --- Артикул (MPN) ---
        self.part_number_edit = QLineEdit()
        layout.addRow("Артикул", self.part_number_edit)

        # --- Количество и цена ---
        qty_price_layout = QHBoxLayout()
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 999999)
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("₽ ")
        qty_price_layout.addWidget(self.quantity_spin)
        qty_price_layout.addWidget(self.price_spin)
        layout.addRow("Кол-во / Цена", qty_price_layout)

        # --- Место хранения (каскад) ---
        location_widget = QWidget()
        location_layout = QHBoxLayout(location_widget)
        location_layout.setContentsMargins(0, 0, 0, 0)
        location_layout.setSpacing(5)
        self.location_place_combo = QComboBox()
        self.location_place_combo.setEditable(True)
        self.location_place_combo.setPlaceholderText("Место")
        self.location_place_combo.setMinimumWidth(100)
        self.location_place_combo.addItems(["", "Дом", "Контора", "Гараж", "Склад"])
        self.location_place_combo.currentTextChanged.connect(self._update_location_containers)
        self.location_container_combo = QComboBox()
        self.location_container_combo.setEditable(True)
        self.location_container_combo.setPlaceholderText("Контейнер")
        self.location_container_combo.setMinimumWidth(120)
        self.location_container_combo.currentTextChanged.connect(self._update_location_shelves)
        self.location_shelf_combo = QComboBox()
        self.location_shelf_combo.setEditable(True)
        self.location_shelf_combo.setPlaceholderText("Полка/Ящик")
        self.location_shelf_combo.setMinimumWidth(100)
        self.location_shelf_combo.currentTextChanged.connect(self._update_location_sections)
        self.location_section_combo = QComboBox()
        self.location_section_combo.setEditable(True)
        self.location_section_combo.setPlaceholderText("Секция/№")
        self.location_section_combo.setMinimumWidth(80)
        location_layout.addWidget(self.location_place_combo)
        location_layout.addWidget(self.location_container_combo)
        location_layout.addWidget(self.location_shelf_combo)
        location_layout.addWidget(self.location_section_combo)
        layout.addRow("Место хранения", location_widget)

        # --- Изображение ---
        image_widget = QWidget()
        image_layout = QHBoxLayout(image_widget)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(5)
        self.image_path_edit = QLineEdit()
        self.image_btn = QPushButton("🖼️ Обзор...")
        self.image_btn.clicked.connect(lambda: self._browse_file(self.image_path_edit, "Images (*.png *.jpg *.jpeg *.gif)"))
        image_layout.addWidget(self.image_path_edit)
        image_layout.addWidget(self.image_btn)
        layout.addRow("Изображение", image_widget)

        # --- Даташит ---
        datasheet_widget = QWidget()
        datasheet_layout = QHBoxLayout(datasheet_widget)
        datasheet_layout.setContentsMargins(0, 0, 0, 0)
        datasheet_layout.setSpacing(5)
        self.datasheet_path_edit = QLineEdit()
        self.datasheet_btn = QPushButton("📄 Обзор...")
        self.datasheet_btn.clicked.connect(lambda: self._browse_file(self.datasheet_path_edit, "PDF (*.pdf)"))
        datasheet_layout.addWidget(self.datasheet_path_edit)
        datasheet_layout.addWidget(self.datasheet_btn)
        layout.addRow("Даташит", datasheet_widget)

        # --- Дата ревизии с кнопкой "Сегодня" ---
        revision_widget = QWidget()
        revision_layout = QHBoxLayout(revision_widget)
        revision_layout.setContentsMargins(0, 0, 0, 0)
        self.revision_date = QDateTimeEdit()
        self.revision_date.setDisplayFormat("dd.MM.yyyy")
        self.revision_date.setCalendarPopup(True)
        today_btn = QPushButton("📅 Сегодня")
        today_btn.clicked.connect(lambda: self.revision_date.setDate(QDate.currentDate()))
        revision_layout.addWidget(self.revision_date)
        revision_layout.addWidget(today_btn)
        layout.addRow("Дата ревизии", revision_widget)

        # --- Заметки ---
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        layout.addRow("Заметки", self.notes_edit)

        # --- Кнопки OK/Cancel ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    # ---------- Парсинг номинала (убрано .0) ----------
    def _parse_and_normalize(self, raw_text: str):
        if not raw_text:
            return None, "", ""
        match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Zμµ]?[a-zA-Z]?)$", raw_text.strip())
        if not match:
            try:
                num = float(raw_text)
                if num.is_integer():
                    num = int(num)
                return num, "", str(num)
            except:
                return None, "", ""
        num_str, unit_raw = match.groups()
        try:
            numeric = float(num_str)
            if numeric.is_integer():
                numeric = int(numeric)
        except:
            return None, "", ""
        unit_lower = unit_raw.lower()
        unit_map = {
            'k': 'кОм', 'm': 'МОм', 'r': 'Ом', 'ohm': 'Ом',
            'n': 'нФ', 'u': 'мкФ', 'p': 'пФ', 'mf': 'мкФ', 'µ': 'мкФ', 'μ': 'мкФ',
            'mhz': 'МГц', 'khz': 'кГц', 'hz': 'Гц',
            'v': 'В', 'mv': 'мВ', 'a': 'А', 'ma': 'мА',
            'h': 'Гн', 'mh': 'мГн'
        }
        unit_full = unit_map.get(unit_lower, unit_raw.upper())
        normalized = f"{numeric} {unit_full}" if unit_full else str(numeric)
        return numeric, unit_full, normalized

    def _on_value_text_changed(self, text):
        num, unit, normalized = self._parse_and_normalize(text)
        if num is not None:
            if unit and self.unit_combo.findText(unit) == -1:
                self.unit_combo.addItem(unit)
            if unit:
                self.unit_combo.setCurrentText(unit)
            self.value_edit.setToolTip(f"Распознано: {normalized}")
        else:
            self.value_edit.setToolTip("Не удалось распознать номинал. Примеры: 10, 2.2, 100")

    # ---------- Собрать название ----------
    def _assemble_name(self):
        category_path = self.category_edit.text().strip()
        category_name = category_path.split('/')[-1].strip() if category_path else ""
        value_raw = self.value_edit.text().strip()
        _, unit, normalized = self._parse_and_normalize(value_raw)
        value_part = normalized if normalized else value_raw
        package = self.package_combo.currentText().strip()
        parts = [p for p in (category_name, value_part, package) if p]
        assembled = " ".join(parts)
        if assembled:
            self.name_edit.setText(assembled)
        else:
            QMessageBox.information(self, "Невозможно собрать", "Заполните хотя бы категорию, номинал или корпус.")

    # ---------- Вспомогательные методы ----------
    def _open_category_selector(self):
        dialog = CategorySelectorDialog(self, db=self.db, selected_category=self.category_edit.text(), start_depth=self.start_depth)
        dialog.category_selected.connect(self.category_edit.setText)
        dialog.exec()

    def _browse_file(self, line_edit, filter_str):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", filter_str)
        if path:
            line_edit.setText(path)

    def _update_location_containers(self, place):
        self.location_container_combo.clear()
        self.location_shelf_combo.clear()
        self.location_section_combo.clear()
        if not place or not self.db:
            return
        containers = set()
        for part in self.db.get_all_parts_filtered():
            loc = part.get('location', '')
            if loc:
                p = [x.strip() for x in loc.split('/')]
                if len(p) >= 2 and p[0] == place:
                    containers.add(p[1])
        self.location_container_combo.addItems([""] + sorted(containers))

    def _update_location_shelves(self, container):
        self.location_shelf_combo.clear()
        self.location_section_combo.clear()
        place = self.location_place_combo.currentText()
        if not place or not container or not self.db:
            return
        shelves = set()
        for part in self.db.get_all_parts_filtered():
            loc = part.get('location', '')
            if loc:
                p = [x.strip() for x in loc.split('/')]
                if len(p) >= 3 and p[0] == place and p[1] == container:
                    shelves.add(p[2])
        self.location_shelf_combo.addItems([""] + sorted(shelves))

    def _update_location_sections(self, shelf):
        self.location_section_combo.clear()
        place = self.location_place_combo.currentText()
        container = self.location_container_combo.currentText()
        if not all([place, container, shelf]) or not self.db:
            return
        sections = set()
        for part in self.db.get_all_parts_filtered():
            loc = part.get('location', '')
            if loc:
                p = [x.strip() for x in loc.split('/')]
                if len(p) >= 4 and p[0] == place and p[1] == container and p[2] == shelf:
                    sections.add(p[3])
        self.location_section_combo.addItems([""] + sorted(sections))

    def _get_category_id_from_path(self, category_path):
        if not category_path or not self.db:
            return None
        cats = self.db.get_categories()
        path_parts = [p.strip() for p in category_path.split('/')]
        target_name = path_parts[-1]
        if len(path_parts) == 1:
            for cat_id, name, parent_id in cats:
                if name == target_name and parent_id in (None, 0):
                    return cat_id
            return None
        item_map = {c[0]: (c[1], c[2]) for c in cats}
        for cat_id, name, parent_id in cats:
            if name != target_name:
                continue
            current_path = []
            current_id = cat_id
            while current_id and current_id in item_map:
                current_name, current_parent_id = item_map[current_id]
                current_path.insert(0, current_name)
                if len(current_path) == len(path_parts):
                    if current_path == path_parts:
                        return cat_id
                    break
                if current_parent_id in (None, 0):
                    break
                current_id = current_parent_id
        return None

    def _build_category_path(self, cat_id, cats):
        if not cat_id:
            return ""
        item_map = {c[0]: (c[1], c[2]) for c in cats}
        path_parts = []
        current_id = cat_id
        while current_id and current_id in item_map:
            name, parent_id = item_map[current_id]
            path_parts.insert(0, name)
            if parent_id in (None, 0):
                break
            current_id = parent_id
        return " / ".join(path_parts)

    def _fill_form(self, data):
        self.name_edit.setText(data.get('name', ''))
        cat_id = data.get('category_id')
        if cat_id:
            cats = self.db.get_categories()
            self.category_edit.setText(self._build_category_path(cat_id, cats))
        else:
            self.category_edit.setText("")
        self.part_type_edit.setText(data.get('part_type', ''))
        self.package_combo.setCurrentText(data.get('package', ''))
        self.manufacturer_edit.setText(data.get('manufacturer', ''))
        self.part_number_edit.setText(data.get('part_number', ''))
        self.quantity_spin.setValue(data.get('quantity', 0))
        self.price_spin.setValue(data.get('price', 0))

        value_numeric = data.get('value_numeric')
        value_unit = data.get('value_unit', '')
        value_raw = data.get('value_raw', '')
        if value_raw:
            self.value_edit.setText(value_raw)
        elif value_numeric is not None and value_unit:
            # Форматируем без .0 для целых
            if isinstance(value_numeric, float) and value_numeric.is_integer():
                self.value_edit.setText(str(int(value_numeric)))
            else:
                self.value_edit.setText(str(value_numeric))
        elif value_numeric is not None:
            if isinstance(value_numeric, float) and value_numeric.is_integer():
                self.value_edit.setText(str(int(value_numeric)))
            else:
                self.value_edit.setText(str(value_numeric))
        if value_unit:
            idx = self.unit_combo.findText(value_unit)
            if idx >= 0:
                self.unit_combo.setCurrentIndex(idx)
            else:
                self.unit_combo.addItem(value_unit)
                self.unit_combo.setCurrentText(value_unit)

        status_val = data.get('status', 'Новое')
        for i in range(self.status_combo.count()):
            txt = self.status_combo.itemText(i)
            clean = txt.split(' ', 1)[-1] if ' ' in txt else txt
            if clean == status_val or txt == status_val:
                self.status_combo.setCurrentIndex(i)
                break

        location = data.get('location', '')
        if location:
            parts = [p.strip() for p in location.split('/')]
            if len(parts) >= 1:
                self.location_place_combo.setCurrentText(parts[0])
                self._update_location_containers(parts[0])
            if len(parts) >= 2:
                self.location_container_combo.setCurrentText(parts[1])
                self._update_location_shelves(parts[1])
            if len(parts) >= 3:
                self.location_shelf_combo.setCurrentText(parts[2])
                self._update_location_sections(parts[2])
            if len(parts) >= 4:
                self.location_section_combo.setCurrentText(parts[3])

        self.image_path_edit.setText(data.get('image_path', ''))
        self.datasheet_path_edit.setText(data.get('datasheet_path', ''))
        if data.get('revision_date'):
            q_date = QDate.fromString(data['revision_date'], "yyyy-MM-dd")
            if q_date.isValid():
                self.revision_date.setDate(q_date)
        self.notes_edit.setPlainText(data.get('notes', ''))

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "⚠️ Наименование обязательно!")
            return
        self.accept()

    def get_location_string(self):
        return ' / '.join([p.strip() for p in [
            self.location_place_combo.currentText(),
            self.location_container_combo.currentText(),
            self.location_shelf_combo.currentText(),
            self.location_section_combo.currentText()
        ] if p.strip()])

    def get_data(self):
        full_status = self.status_combo.currentText()
        status_value = full_status.split(' ', 1)[-1] if ' ' in full_status else full_status
        category_path = self.category_edit.text().strip()
        category_id = self._get_category_id_from_path(category_path) if category_path else None
        raw_value = self.value_edit.text().strip()
        numeric, unit, normalized = self._parse_and_normalize(raw_value)
        if numeric is None and self.unit_combo.currentText():
            match = re.search(r"([0-9]+(?:\.[0-9]+)?)", raw_value)
            if match:
                numeric = float(match.group(1))
                if numeric.is_integer():
                    numeric = int(numeric)
                unit = self.unit_combo.currentText()
        value_raw = raw_value if raw_value else None

        return {
            'name': self.name_edit.text().strip(),
            'category_id': category_id,
            'part_type': self.part_type_edit.text().strip(),
            'package': self.package_combo.currentText(),
            'manufacturer': self.manufacturer_edit.text().strip(),
            'part_number': self.part_number_edit.text().strip(),
            'quantity': self.quantity_spin.value(),
            'price': self.price_spin.value(),
            'location': self.get_location_string(),
            'status': status_value,
            'image_path': self.image_path_edit.text().strip(),
            'datasheet_path': self.datasheet_path_edit.text().strip(),
            'revision_date': self.revision_date.date().toString("yyyy-MM-dd") if self.revision_date.date().isValid() else None,
            'notes': self.notes_edit.toPlainText().strip(),
            'value_numeric': numeric,
            'value_unit': unit if unit else None,
            'value_raw': value_raw
        }