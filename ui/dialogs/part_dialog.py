# ui/dialogs/part_dialog.py
import logging
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QDateTimeEdit, QTextEdit, QDialogButtonBox, QMessageBox, QFileDialog,
    QWidget, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt, QDate

logger = logging.getLogger(__name__)

class PartDialog(QDialog):
    def __init__(self, parent=None, part_data=None, db=None):
        super().__init__(parent)
        self.db = db
        self.part_data = part_data
        self.setWindowTitle("✏️ Редактирование компонента")
        self.setMinimumWidth(550)
        self._init_ui()
        if part_data:
            self._fill_form(part_data)
    
    def _init_ui(self):
        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        self.name_edit = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.setPlaceholderText("Выберите или введите")
        if self.db:
            cats = self.db.get_categories()
            self.category_combo.addItems([""] + [c[1] for c in cats])
        
        self.part_type_edit = QLineEdit()
        self.package_combo = QComboBox()
        self.package_combo.setEditable(True)
        self.package_combo.addItems(["0402", "0603", "0805", "1206", "SOT-23", "SOIC-8", "DIP-8", "TQFP-48"])
        
        # === СОСТОЯНИЕ (ВЫПАДАЮЩИЙ СПИСОК, НЕ РЕДАКТИРУЕМЫЙ) ===
        self.status_combo = QComboBox()
        self.status_combo.setEditable(False)
        self.status_combo.addItems([
            "🛒 Новое", "ℹ️ Б/У проверено", "❓ Б/У не проверено",
            "✅ Отличное", "✔️ Хорошее", "🚫 Плохое", "❌ Неисправно"
        ])
        self.status_combo.setCurrentText("🛒 Новое")
        
        self.manufacturer_edit = QLineEdit()
        self.part_number_edit = QLineEdit()
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 999999)
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("₽ ")
        
        # === ЧЕТЫРЕХУРОВНЕВОЕ МЕСТО ХРАНЕНИЯ ===
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
        
        self.image_path_edit = QLineEdit()
        self.image_btn = QPushButton("🖼️ Обзор...")
        self.image_btn.clicked.connect(lambda: self._browse_file(self.image_path_edit, "Images (*.png *.jpg *.jpeg *.gif)"))
        
        self.datasheet_path_edit = QLineEdit()
        self.datasheet_btn = QPushButton("📄 Обзор...")
        self.datasheet_btn.clicked.connect(lambda: self._browse_file(self.datasheet_path_edit, "PDF (*.pdf)"))
        
        self.revision_date = QDateTimeEdit()
        self.revision_date.setDisplayFormat("dd.MM.yyyy")
        self.revision_date.setCalendarPopup(True)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        
        layout.addRow("Наименование *", self.name_edit)
        layout.addRow("Категория", self.category_combo)
        layout.addRow("Тип детали", self.part_type_edit)
        layout.addRow("Корпус", self.package_combo)
        layout.addRow("📍 Состояние", self.status_combo)
        layout.addRow("Производитель", self.manufacturer_edit)
        layout.addRow("Артикул", self.part_number_edit)
        
        qty_price = QHBoxLayout()
        qty_price.addWidget(self.quantity_spin)
        qty_price.addWidget(self.price_spin)
        layout.addRow("Кол-во / Цена", qty_price)
        
        layout.addRow("📍 Место хранения", location_widget)
        
        media_layout = QHBoxLayout()
        media_layout.addWidget(self.image_path_edit)
        media_layout.addWidget(self.image_btn)
        layout.addRow("Изображение", media_layout)
        
        media_layout2 = QHBoxLayout()
        media_layout2.addWidget(self.datasheet_path_edit)
        media_layout2.addWidget(self.datasheet_btn)
        layout.addRow("Даташит", media_layout2)
        
        layout.addRow("Дата ревизии", self.revision_date)
        layout.addRow("Заметки", self.notes_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def _browse_file(self, line_edit, filter_str):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", filter_str)
        if path: line_edit.setText(path)
    
    def _update_location_containers(self, place):
        self.location_container_combo.clear()
        self.location_shelf_combo.clear()
        self.location_section_combo.clear()
        if not place: return
        if self.db:
            containers = set()
            parts = self.db.get_all_parts_filtered()
            for part in parts:
                location = part.get('location', '')
                if location:
                    p = [x.strip() for x in location.split('/')]
                    if len(p) >= 2 and p[0] == place: containers.add(p[1])
            self.location_container_combo.addItems([""] + sorted(containers))
    
    def _update_location_shelves(self, container):
        self.location_shelf_combo.clear()
        self.location_section_combo.clear()
        place = self.location_place_combo.currentText()
        if not place or not container: return
        if self.db:
            shelves = set()
            parts = self.db.get_all_parts_filtered()
            for part in parts:
                location = part.get('location', '')
                if location:
                    p = [x.strip() for x in location.split('/')]
                    if len(p) >= 3 and p[0] == place and p[1] == container: shelves.add(p[2])
            self.location_shelf_combo.addItems([""] + sorted(shelves))

    def _update_location_sections(self, section):
        self.location_section_combo.clear()
        place = self.location_place_combo.currentText()
        container = self.location_container_combo.currentText()
        shelf = self.location_shelf_combo.currentText()
        if not all([place, container, shelf]): return
        if self.db:
            sections = set()
            parts = self.db.get_all_parts_filtered()
            for part in parts:
                location = part.get('location', '')
                if location:
                    p = [x.strip() for x in location.split('/')]
                    if len(p) >= 4 and p[0] == place and p[1] == container and p[2] == shelf: sections.add(p[3])
            self.location_section_combo.addItems([""] + sorted(sections))
    
    def _fill_form(self, data):
        self.name_edit.setText(data.get('name', ''))
        self.part_type_edit.setText(data.get('part_type', ''))
        self.package_combo.setCurrentText(data.get('package', ''))
        self.manufacturer_edit.setText(data.get('manufacturer', ''))
        self.part_number_edit.setText(data.get('part_number', ''))
        self.quantity_spin.setValue(data.get('quantity', 0))
        self.price_spin.setValue(data.get('price', 0))
        
        status_val = data.get('status', 'Новое')
        found = False
        for i in range(self.status_combo.count()):
            item_text = self.status_combo.itemText(i)
            clean_item = item_text.split(' ', 1)[-1] if ' ' in item_text else item_text
            clean_status = status_val.split(' ', 1)[-1] if ' ' in status_val else status_val
            if clean_item == clean_status or item_text == status_val:
                self.status_combo.setCurrentIndex(i)
                found = True
                break
        if not found: self.status_combo.setCurrentIndex(0)
        
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
        
        rev_date_str = data.get('revision_date')
        if rev_date_str:
            q_date = QDate.fromString(rev_date_str, "yyyy-MM-dd")
            if q_date.isValid(): self.revision_date.setDate(q_date)
    
    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "⚠️ Наименование обязательно!")
            return
        self.accept()
    
    def get_location_string(self):
        place = self.location_place_combo.currentText().strip()
        container = self.location_container_combo.currentText().strip()
        shelf = self.location_shelf_combo.currentText().strip()
        section = self.location_section_combo.currentText().strip()
        parts = [p for p in [place, container, shelf, section] if p]
        return ' / '.join(parts) if parts else ''
    
    def get_data(self):
        full_status = self.status_combo.currentText()
        status_value = full_status.split(' ', 1)[-1] if ' ' in full_status else full_status
        
        return {
            'name': self.name_edit.text().strip(),
            'category': self.category_combo.currentText(),
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
            'notes': self.notes_edit.toPlainText().strip()
        }