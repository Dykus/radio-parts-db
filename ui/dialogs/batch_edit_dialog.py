# ui/dialogs/batch_edit_dialog.py
import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QLineEdit, QDoubleSpinBox, QSpinBox, QRadioButton, QButtonGroup,
    QPushButton, QMessageBox, QLabel
)
from PySide6.QtCore import Qt

class BatchEditDialog(QDialog):
    def __init__(self, parent, part_ids, db):
        super().__init__(parent)
        self.part_ids = part_ids
        self.db = db
        self.setWindowTitle(f"Пакетное редактирование (выбрано {len(part_ids)} деталей)")
        self.setMinimumWidth(550)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # ---- Категория ----
        cat_layout = QHBoxLayout()
        self.cat_combo = QComboBox()
        self.cat_combo.addItem("— Не менять —", None)
        self.cat_combo.addItem("Выбрать категорию...", "select")
        self.cat_combo.currentIndexChanged.connect(self._on_cat_combo_changed)
        cat_layout.addWidget(QLabel("Категория:"))
        cat_layout.addWidget(self.cat_combo)
        self.cat_path_edit = QLineEdit()
        self.cat_path_edit.setReadOnly(True)
        self.cat_path_edit.setPlaceholderText("Не выбрана")
        self.cat_path_edit.setVisible(False)
        cat_layout.addWidget(self.cat_path_edit)
        layout.addLayout(cat_layout)

        # ---- Место хранения ----
        loc_layout = QHBoxLayout()
        self.loc_combo = QComboBox()
        self.loc_combo.addItem("— Не менять —", None)
        self.loc_combo.addItem("Установить место...", "set")
        self.loc_combo.currentIndexChanged.connect(self._on_loc_combo_changed)
        loc_layout.addWidget(QLabel("Место:"))
        loc_layout.addWidget(self.loc_combo)
        self.loc_edit = QLineEdit()
        self.loc_edit.setPlaceholderText("Введите место (например: Дом / Шкаф / Полка)")
        self.loc_edit.setVisible(False)
        loc_layout.addWidget(self.loc_edit)
        layout.addLayout(loc_layout)

        # ---- Статус ----
        status_layout = QHBoxLayout()
        self.status_combo = QComboBox()
        self.status_combo.addItem("— Не менять —", None)
        self.status_combo.addItems(["Новое", "Б/У проверено", "Б/У не проверено", "Отличное", "Хорошее", "Плохое", "Неисправно"])
        status_layout.addWidget(QLabel("Статус:"))
        status_layout.addWidget(self.status_combo)
        layout.addLayout(status_layout)

        # ---- Тип детали ----
        type_layout = QHBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItem("— Не менять —", None)
        self.type_combo.setEditable(True)
        self.type_combo.setPlaceholderText("Введите или выберите тип")
        type_layout.addWidget(QLabel("Тип детали:"))
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # ---- Производитель ----
        manuf_layout = QHBoxLayout()
        self.manuf_combo = QComboBox()
        self.manuf_combo.addItem("— Не менять —", None)
        self.manuf_combo.setEditable(True)
        self.manuf_combo.setPlaceholderText("Введите или выберите производителя")
        manuf_layout.addWidget(QLabel("Производитель:"))
        manuf_layout.addWidget(self.manuf_combo)
        layout.addLayout(manuf_layout)

        # ---- Номинал (новая группа) ----
        nominal_group = QGroupBox("Номинал")
        nominal_layout = QVBoxLayout(nominal_group)
        self.nominal_radio_no = QRadioButton("Не менять")
        self.nominal_radio_no.setChecked(True)
        self.nominal_radio_set = QRadioButton("Установить:")
        nominal_value_layout = QHBoxLayout()
        self.nominal_value_edit = QDoubleSpinBox()
        self.nominal_value_edit.setRange(-999999, 999999)
        self.nominal_value_edit.setDecimals(6)
        self.nominal_value_edit.setPrefix("")
        self.nominal_unit_combo = QComboBox()
        self.nominal_unit_combo.setEditable(True)
        self.nominal_unit_combo.addItems(["", "Ом", "кОм", "МОм", "пФ", "нФ", "мкФ", "Ф", "мкГн", "мГн", "Гн", "В", "А", "мА", "мВ", "шт"])
        nominal_value_layout.addWidget(self.nominal_value_edit)
        nominal_value_layout.addWidget(self.nominal_unit_combo)
        nominal_layout.addWidget(self.nominal_radio_no)
        nominal_layout.addWidget(self.nominal_radio_set)
        nominal_layout.addLayout(nominal_value_layout)
        layout.addWidget(nominal_group)

        # ---- Цена ----
        price_group = QGroupBox("Цена")
        price_layout = QVBoxLayout(price_group)
        self.price_radio_no = QRadioButton("Не менять")
        self.price_radio_no.setChecked(True)
        self.price_radio_set = QRadioButton("Установить:")
        self.price_radio_add = QRadioButton("Увеличить на:")
        self.price_radio_sub = QRadioButton("Уменьшить на:")
        self.price_edit = QDoubleSpinBox()
        self.price_edit.setRange(-999999, 999999)
        self.price_edit.setDecimals(2)
        self.price_edit.setSuffix(" ₽")
        price_layout.addWidget(self.price_radio_no)
        price_layout.addWidget(self.price_radio_set)
        price_layout.addWidget(self.price_radio_add)
        price_layout.addWidget(self.price_radio_sub)
        price_layout.addWidget(self.price_edit)
        layout.addWidget(price_group)

        # ---- Количество ----
        qty_group = QGroupBox("Количество")
        qty_layout = QVBoxLayout(qty_group)
        self.qty_radio_no = QRadioButton("Не менять")
        self.qty_radio_no.setChecked(True)
        self.qty_radio_set = QRadioButton("Установить:")
        self.qty_radio_add = QRadioButton("Добавить:")
        self.qty_radio_sub = QRadioButton("Отнять:")
        self.qty_edit = QSpinBox()
        self.qty_edit.setRange(-999999, 999999)
        qty_layout.addWidget(self.qty_radio_no)
        qty_layout.addWidget(self.qty_radio_set)
        qty_layout.addWidget(self.qty_radio_add)
        qty_layout.addWidget(self.qty_radio_sub)
        qty_layout.addWidget(self.qty_edit)
        layout.addWidget(qty_group)

        # ---- Кнопки ----
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("Применить")
        self.btn_cancel = QPushButton("Отмена")
        self.btn_ok.clicked.connect(self._apply)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        # Заполняем комбобоксы существующими значениями
        self._load_comboboxes()

    def _load_comboboxes(self):
        # Типы деталей
        types = set(self.db.get_dictionary_values('part_type'))
        for part in self.db.get_all_parts_filtered():
            t = part.get('part_type')
            if t:
                types.add(t)
        for t in sorted(types):
            self.type_combo.addItem(t)
        # Производители
        mans = set(self.db.get_dictionary_values('manufacturer'))
        for part in self.db.get_all_parts_filtered():
            m = part.get('manufacturer')
            if m:
                mans.add(m)
        for m in sorted(mans):
            self.manuf_combo.addItem(m)

    def _on_cat_combo_changed(self, idx):
        if self.cat_combo.currentData() == "select":
            from .category_selector import CategorySelectorDialog
            dialog = CategorySelectorDialog(self, db=self.db, start_depth=1)
            dialog.category_selected.connect(self._set_category)
            dialog.exec()
            if self.cat_combo.currentData() == "select":
                self.cat_combo.setCurrentIndex(0)

    def _set_category(self, path):
        existing_index = -1
        for i in range(self.cat_combo.count()):
            if self.cat_combo.itemData(i) == path:
                existing_index = i
                break
        if existing_index == -1:
            self.cat_combo.insertItem(2, f"📁 {path}", path)
            existing_index = 2
        self.cat_combo.setCurrentIndex(existing_index)
        self.cat_path_edit.setVisible(False)

    def _on_loc_combo_changed(self, idx):
        if self.loc_combo.currentData() == "set":
            self.loc_edit.setVisible(True)
        else:
            self.loc_edit.setVisible(False)

    def _apply(self):
        updates = {}
        errors = []

        # Категория
        cat_data = self.cat_combo.currentData()
        if cat_data and cat_data != "select" and cat_data is not None:
            cat_id = self._get_category_id_from_path(cat_data)
            if cat_id is None:
                errors.append(f"Категория '{cat_data}' не найдена в базе.")
            else:
                updates['category_id'] = cat_id

        # Место
        if self.loc_edit.isVisible() and self.loc_edit.text():
            updates['location'] = self.loc_edit.text().strip()

        # Статус
        if self.status_combo.currentData() is not None:
            updates['status'] = self.status_combo.currentText()

        # Тип детали
        if self.type_combo.currentIndex() > 0:
            new_type = self.type_combo.currentText().strip()
            if new_type:
                updates['part_type'] = new_type
                self.db.add_dictionary_value('part_type', new_type)

        # Производитель
        if self.manuf_combo.currentIndex() > 0:
            new_manuf = self.manuf_combo.currentText().strip()
            if new_manuf:
                updates['manufacturer'] = new_manuf
                self.db.add_dictionary_value('manufacturer', new_manuf)

        # Номинал
        if self.nominal_radio_set.isChecked():
            numeric = self.nominal_value_edit.value()
            unit = self.nominal_unit_combo.currentText().strip()
            if unit:
                updates['value_numeric'] = numeric
                updates['value_unit'] = unit
                updates['value_raw'] = f"{numeric} {unit}"
            else:
                errors.append("Для изменения номинала необходимо указать единицу измерения.")

        # Цена
        price_value = self.price_edit.value()
        if self.price_radio_set.isChecked():
            updates['price_operation'] = ('set', price_value)
        elif self.price_radio_add.isChecked():
            updates['price_operation'] = ('add', price_value)
        elif self.price_radio_sub.isChecked():
            updates['price_operation'] = ('sub', price_value)

        # Количество
        qty_value = self.qty_edit.value()
        if self.qty_radio_set.isChecked():
            updates['quantity_operation'] = ('set', qty_value)
        elif self.qty_radio_add.isChecked():
            updates['quantity_operation'] = ('add', qty_value)
        elif self.qty_radio_sub.isChecked():
            updates['quantity_operation'] = ('sub', qty_value)

        if errors:
            QMessageBox.warning(self, "Ошибка", "\n".join(errors))
            return

        # Применяем обновления к каждой детали
        for part_id in self.part_ids:
            part = self.db.get_part(part_id)
            if not part:
                continue
            new_data = part.copy()
            # Простые поля
            for key in ['category_id', 'location', 'status', 'part_type', 'manufacturer']:
                if key in updates:
                    new_data[key] = updates[key]
            # Номинал
            if 'value_numeric' in updates:
                new_data['value_numeric'] = updates['value_numeric']
                new_data['value_unit'] = updates['value_unit']
                new_data['value_raw'] = updates['value_raw']
            # Цена
            if 'price_operation' in updates:
                op, val = updates['price_operation']
                if op == 'set':
                    new_data['price'] = val
                elif op == 'add':
                    new_data['price'] = part.get('price', 0) + val
                elif op == 'sub':
                    new_data['price'] = part.get('price', 0) - val
                if new_data['price'] < 0:
                    new_data['price'] = 0
            # Количество
            if 'quantity_operation' in updates:
                op, val = updates['quantity_operation']
                if op == 'set':
                    new_data['quantity'] = max(0, val)
                elif op == 'add':
                    new_data['quantity'] = max(0, part.get('quantity', 0) + val)
                elif op == 'sub':
                    new_data['quantity'] = max(0, part.get('quantity', 0) - val)

            self.db.update_part(part_id, new_data)

        self.accept()

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