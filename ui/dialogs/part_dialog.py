# ui/dialogs/part_dialog.py
import re
import logging
import uuid
import shutil
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QDateTimeEdit, QTextEdit, QDialogButtonBox, QMessageBox, QFileDialog,
    QWidget, QHBoxLayout, QPushButton, QLabel, QFrame, QVBoxLayout,
    QTabWidget, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap, QFont
from ui.dialogs.category_selector import CategorySelectorDialog
from config import DATA_DIR

# Попытка импорта Pillow для обработки изображений
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    logging.getLogger(__name__).warning("Pillow не установлен. Сжатие изображений отключено. Установите: pip install Pillow")

logger = logging.getLogger(__name__)


class PartDialog(QDialog):
    """Диалог редактирования/добавления компонента.
    Три вкладки: Основная информация, Изображения и даташит, Заметки."""

    def __init__(self, parent=None, part_data=None, db=None, start_depth=0):
        super().__init__(parent)
        self.db = db
        self.part_data = part_data
        self.start_depth = start_depth
        self.notes_font_size = 10  # размер шрифта заметок по умолчанию
        self.setWindowTitle("✏️ Редактирование компонента")
        self.setMinimumSize(820, 580)
        self.resize(860, 640)
        self.image_widgets = []  # список (frame, file_path) для выбранных локальных изображений
        self._init_ui()
        if part_data:
            self._fill_form(part_data)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # ===== QTabWidget: 3 вкладки =====
        self.tabs = QTabWidget()

        # ====================================================================
        # ВКЛАДКА 1: Основная информация + две колонки
        # ====================================================================
        tab1_widget = QWidget()
        tab1_layout = QVBoxLayout(tab1_widget)
        tab1_layout.setContentsMargins(8, 8, 8, 8)
        tab1_layout.setSpacing(8)

        # --- Блок «Основная информация» на всю ширину ---
        basic_group = QGroupBox("📋 Основная информация")
        basic_form = QFormLayout(basic_group)
        basic_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        basic_form.setSpacing(8)

        # Наименование
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Можно ввести вручную или нажать «Собрать название»")
        basic_form.addRow("Наименование *", self.name_edit)

        # Категория
        cat_widget = QWidget()
        cat_layout = QHBoxLayout(cat_widget)
        cat_layout.setContentsMargins(0, 0, 0, 0)
        cat_layout.setSpacing(5)
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("Выберите категорию")
        self.category_edit.setReadOnly(True)
        self.btn_select_category = QPushButton("📂 ...")
        self.btn_select_category.setMaximumWidth(40)
        self.btn_select_category.clicked.connect(self._open_category_selector)
        cat_layout.addWidget(self.category_edit)
        cat_layout.addWidget(self.btn_select_category)
        basic_form.addRow("Категория", cat_widget)

        # Тип детали
        self.part_type_combo = QComboBox()
        self.part_type_combo.setEditable(True)
        self.part_type_combo.setPlaceholderText("Введите или выберите тип детали")
        basic_form.addRow("Тип детали", self.part_type_combo)

        # Номинал / значение
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
        nominal_layout.addWidget(self.value_edit)
        nominal_layout.addWidget(self.unit_combo)
        basic_form.addRow("Номинал / значение", nominal_widget)

        # Кнопка «Собрать название»
        self.btn_assemble = QPushButton(" Собрать название")
        self.btn_assemble.clicked.connect(self._assemble_name)
        basic_form.addRow("", self.btn_assemble)

        tab1_layout.addWidget(basic_group)

        # --- Сплиттер с двумя колонками ---
        splitter = QSplitter(Qt.Horizontal)

        # Левая колонка: Характеристики + Производитель + Габариты
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        specs_group = QGroupBox("⚙️ Характеристики")
        specs_form = QFormLayout(specs_group)
        specs_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.package_combo = QComboBox()
        self.package_combo.setEditable(True)
        self.package_combo.addItems(["", "0402", "0603", "0805", "1206", "SOT-23", "SOIC-8", "DIP-8", "TQFP-48", "TO-92", "TO-220"])
        specs_form.addRow("Корпус", self.package_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Новое", "Б/У проверено", "Б/У не проверено", "Отличное", "Хорошее", "Плохое", "Неисправно"])
        self.status_combo.setCurrentText("Новое")
        specs_form.addRow("Состояние", self.status_combo)

        self.part_number_edit = QLineEdit()
        specs_form.addRow("Артикул", self.part_number_edit)
        left_layout.addWidget(specs_group)

        manuf_group = QGroupBox("🏭 Производитель")
        manuf_form = QFormLayout(manuf_group)
        self.manufacturer_combo = QComboBox()
        self.manufacturer_combo.setEditable(True)
        self.manufacturer_combo.setPlaceholderText("Введите или выберите производителя")
        manuf_form.addRow("Производитель", self.manufacturer_combo)
        left_layout.addWidget(manuf_group)

        # Сворачиваемая группа «Габариты конденсаторов» - БЕЗ чекбокса
        # Видимость управляется автоматически через _show_dims_for_capacitor()
        self.dims_group = QGroupBox("📏 Габариты (для конденсаторов)")
        self.dims_group.setVisible(False)  # скрыта по умолчанию
        dims_form = QFormLayout(self.dims_group)
        dims_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.diameter_spin = QDoubleSpinBox()
        self.diameter_spin.setRange(0, 100)
        self.diameter_spin.setDecimals(1)
        self.diameter_spin.setSuffix(" мм")
        dims_form.addRow("Диаметр (мм)", self.diameter_spin)

        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(0, 200)
        self.height_spin.setDecimals(1)
        self.height_spin.setSuffix(" мм")
        dims_form.addRow("Высота (мм)", self.height_spin)

        self.lead_pitch_spin = QDoubleSpinBox()
        self.lead_pitch_spin.setRange(0, 50)
        self.lead_pitch_spin.setDecimals(1)
        self.lead_pitch_spin.setSuffix(" мм")
        dims_form.addRow("Шаг выводов (мм)", self.lead_pitch_spin)

        self.lead_diameter_spin = QDoubleSpinBox()
        self.lead_diameter_spin.setRange(0, 5)
        self.lead_diameter_spin.setDecimals(2)
        self.lead_diameter_spin.setSuffix(" мм")
        dims_form.addRow("Толщина выводов (мм)", self.lead_diameter_spin)
        left_layout.addWidget(self.dims_group)

        left_layout.addStretch()
        splitter.addWidget(left_widget)

        # Правая колонка: Склад
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        stock_group = QGroupBox("📦 Склад и количество")
        stock_form = QFormLayout(stock_group)
        stock_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        qty_price_widget = QWidget()
        qty_price_layout = QHBoxLayout(qty_price_widget)
        qty_price_layout.setContentsMargins(0, 0, 0, 0)
        qty_price_layout.setSpacing(5)
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 999999)
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("₽  ")
        qty_price_layout.addWidget(self.quantity_spin)
        qty_price_layout.addWidget(self.price_spin)
        stock_form.addRow("Кол-во / Цена", qty_price_widget)

        # Место хранения: 4 комбобокса в строку
        place_widget = QWidget()
        place_layout = QHBoxLayout(place_widget)
        place_layout.setContentsMargins(0, 0, 0, 0)
        place_layout.setSpacing(4)
        self.location_place_combo = QComboBox()
        self.location_place_combo.setEditable(True)
        self.location_place_combo.setPlaceholderText("Место")
        self.location_place_combo.addItems(["", "Дом", "Контора", "Гараж", "Склад"])
        self.location_place_combo.currentTextChanged.connect(self._update_location_containers)

        self.location_container_combo = QComboBox()
        self.location_container_combo.setEditable(True)
        self.location_container_combo.setPlaceholderText("Контейнер")
        self.location_container_combo.currentTextChanged.connect(self._update_location_shelves)

        self.location_shelf_combo = QComboBox()
        self.location_shelf_combo.setEditable(True)
        self.location_shelf_combo.setPlaceholderText("Полка/Ящик")
        self.location_shelf_combo.currentTextChanged.connect(self._update_location_sections)

        self.location_section_combo = QComboBox()
        self.location_section_combo.setEditable(True)
        self.location_section_combo.setPlaceholderText("Секция/№")

        for cb in [self.location_place_combo, self.location_container_combo,
                   self.location_shelf_combo, self.location_section_combo]:
            place_layout.addWidget(cb)
        stock_form.addRow("Место хранения", place_widget)

        # Дата ревизии
        revision_widget = QWidget()
        revision_layout = QHBoxLayout(revision_widget)
        revision_layout.setContentsMargins(0, 0, 0, 0)
        self.revision_date = QDateTimeEdit()
        self.revision_date.setDisplayFormat("dd.MM.yyyy")
        self.revision_date.setCalendarPopup(True)
        today_btn = QPushButton(" Сегодня")
        today_btn.clicked.connect(lambda: self.revision_date.setDate(QDate.currentDate()))
        revision_layout.addWidget(self.revision_date)
        revision_layout.addWidget(today_btn)
        stock_form.addRow("Дата ревизии", revision_widget)

        right_layout.addWidget(stock_group)
        right_layout.addStretch()

        splitter.addWidget(right_widget)
        splitter.setSizes([380, 380])
        tab1_layout.addWidget(splitter, 1)  # растягивается

        self.tabs.addTab(tab1_widget, " Основная информация")

        # ====================================================================
        # ВКЛАДКА 2: Изображения и даташит
        # ====================================================================
        tab2_widget = QWidget()
        tab2_layout = QVBoxLayout(tab2_widget)
        tab2_layout.setContentsMargins(12, 12, 12, 12)
        tab2_layout.setSpacing(12)

        # --- Изображения ---
        img_group = QGroupBox("🖼️ Изображения (до 3)")
        img_layout = QVBoxLayout(img_group)
        img_layout.setSpacing(8)

        img_info = QLabel("Можно добавить до 3 локальных изображений. Они будут сжаты в WebP.")
        img_info.setStyleSheet("color: #666; font-style: italic; font-size: 10pt;")
        img_layout.addWidget(img_info)

        # Кнопка добавления — компактная, не на всю ширину
        img_btn_widget = QWidget()
        img_btn_layout = QHBoxLayout(img_btn_widget)
        img_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.img_btn = QPushButton("️ Добавить изображения")
        self.img_btn.setStyleSheet("""
            QPushButton {
                background-color: #3399ff; color: white; border: none;
                border-radius: 4px; padding: 6px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #1f6fa0; }
        """)
        self.img_btn.setMinimumHeight(32)
        self.img_btn.clicked.connect(self._add_images)
        img_btn_layout.addWidget(self.img_btn)
        img_btn_layout.addStretch()
        img_layout.addWidget(img_btn_widget)

        # Контейнер для превью
        img_preview_widget = QWidget()
        self.img_container_layout = QHBoxLayout(img_preview_widget)
        self.img_container_layout.setSpacing(12)
        self.img_container_layout.setAlignment(Qt.AlignLeft)
        img_layout.addWidget(img_preview_widget)
        img_layout.addStretch()

        self.img_container = img_preview_widget
        tab2_layout.addWidget(img_group, 1)

        # --- Даташит ---
        ds_group = QGroupBox("📄 Даташит")
        ds_layout = QVBoxLayout(ds_group)
        ds_layout.setSpacing(8)

        ds_info = QLabel("Укажите путь к PDF-файлу даташита. Можно выбрать локальный файл.")
        ds_info.setStyleSheet("color: #666; font-style: italic; font-size: 10pt;")
        ds_info.setWordWrap(True)
        ds_layout.addWidget(ds_info)

        ds_path_widget = QWidget()
        ds_path_layout = QHBoxLayout(ds_path_widget)
        ds_path_layout.setContentsMargins(0, 0, 0, 0)
        self.datasheet_path_edit = QLineEdit()
        self.datasheet_path_edit.setPlaceholderText("Путь к PDF...")
        self.datasheet_btn = QPushButton("📄 Обзор...")
        self.datasheet_btn.clicked.connect(lambda: self._browse_file(self.datasheet_path_edit, "PDF (*.pdf)"))
        ds_path_layout.addWidget(self.datasheet_path_edit)
        ds_path_layout.addWidget(self.datasheet_btn)
        ds_layout.addWidget(ds_path_widget)

        tab2_layout.addWidget(ds_group, 1)

        self.tabs.addTab(tab2_widget, "🖼️ Изображения и даташит")

        # ====================================================================
        # ВКЛАДКА 3: Заметки
        # ====================================================================
        tab3_widget = QWidget()
        tab3_layout = QVBoxLayout(tab3_widget)
        tab3_layout.setContentsMargins(12, 12, 12, 12)

        # Toolbar для шрифта заметок
        notes_toolbar = QWidget()
        notes_toolbar_layout = QHBoxLayout(notes_toolbar)
        notes_toolbar_layout.setContentsMargins(0, 0, 0, 5)

        self.notes_font_size_label = QLabel("Размер шрифта:")
        self.notes_font_decrease_btn = QPushButton("A-")
        self.notes_font_decrease_btn.setFixedSize(32, 24)
        self.notes_font_decrease_btn.clicked.connect(lambda: self._change_notes_font(-1))

        self.notes_font_size_display = QLabel(str(self.notes_font_size))
        self.notes_font_size_display.setMinimumWidth(30)
        self.notes_font_size_display.setAlignment(Qt.AlignCenter)
        self.notes_font_size_display.setStyleSheet("font-weight: bold;")

        self.notes_font_increase_btn = QPushButton("A+")
        self.notes_font_increase_btn.setFixedSize(32, 24)
        self.notes_font_increase_btn.clicked.connect(lambda: self._change_notes_font(1))

        self.notes_font_reset_btn = QPushButton("🔄 Сброс")
        self.notes_font_reset_btn.clicked.connect(lambda: self._reset_notes_font())

        notes_toolbar_layout.addWidget(self.notes_font_size_label)
        notes_toolbar_layout.addWidget(self.notes_font_decrease_btn)
        notes_toolbar_layout.addWidget(self.notes_font_size_display)
        notes_toolbar_layout.addWidget(self.notes_font_increase_btn)
        notes_toolbar_layout.addWidget(self.notes_font_reset_btn)
        notes_toolbar_layout.addStretch()
        tab3_layout.addWidget(notes_toolbar)

        # Поле заметок
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Введите заметки здесь...")
        self.notes_edit.setStyleSheet("background-color: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; padding: 6px;")
        # Устанавливаем шрифт по умолчанию
        notes_font = QFont(self.notes_edit.font())
        notes_font.setPointSize(self.notes_font_size)
        self.notes_edit.setFont(notes_font)
        tab3_layout.addWidget(self.notes_edit, 1)

        self.tabs.addTab(tab3_widget, "📝 Заметки")

        layout.addWidget(self.tabs, 1)  # вкладки занимают всё свободное место

        # ===== Кнопки OK / Cancel (всегда видны снизу) =====
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet("""
            QPushButton {
                padding: 6px 20px;
                font-weight: bold;
                min-width: 90px;
            }
        """)
        layout.addWidget(buttons)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

        # Загрузка выпадающих списков и применение стилей
        self._load_comboboxes()
        self._apply_combobox_styles()
        self._disable_spinbox_wheel()

    # --------------------------------------------------------------------------
    # Управление шрифтом заметок
    # --------------------------------------------------------------------------
    def _change_notes_font(self, delta):
        """Изменяет размер шрифта в поле заметок на delta пунктов."""
        new_size = self.notes_font_size + delta
        if 6 <= new_size <= 72:
            self.notes_font_size = new_size
            self.notes_font_size_display.setText(str(new_size))
            font = QFont(self.notes_edit.font())
            font.setPointSize(new_size)
            self.notes_edit.setFont(font)

    def _reset_notes_font(self):
        """Сбрасывает размер шрифта заметок к значению по умолчанию."""
        self.notes_font_size = 10
        self.notes_font_size_display.setText("10")
        font = QFont(self.notes_edit.font())
        font.setPointSize(10)
        self.notes_edit.setFont(font)

    # --------------------------------------------------------------------------
    # Стили и защита spinbox'ов
    # --------------------------------------------------------------------------
    def _apply_combobox_styles(self):
        """Применяет стили для комбобоксов с видимой стрелочкой через SVG."""
        combo_style = """
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #a0a0a0;
                border-radius: 3px;
                padding: 4px 8px;
                min-height: 20px;
            }
            QComboBox:hover { border: 1px solid #3399ff; }
            QComboBox:focus { border: 1px solid #3399ff; }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 22px;
                border-left: 1px solid #a0a0a0;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: #e8e8e8;
            }
            QComboBox::drop-down:hover { background-color: #d8d8d8; }
            QComboBox::down-arrow {
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'><path fill='%23333333' d='M2 4l4 4 4-4z'/></svg>");
                width: 12px;
                height: 12px;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #a0a0a0;
                selection-background-color: #3399ff;
                selection-color: #ffffff;
                padding: 2px;
            }
        """
        for combo in self.findChildren(QComboBox):
            combo.setStyleSheet(combo_style)

    def _disable_spinbox_wheel(self):
        """Отключает изменение значений колёсиком мыши у всех QSpinBox/QDoubleSpinBox."""
        for spinbox in self.findChildren(QSpinBox):
            spinbox.setFocusPolicy(Qt.StrongFocus)
        for spinbox in self.findChildren(QDoubleSpinBox):
            spinbox.setFocusPolicy(Qt.StrongFocus)

    # --------------------------------------------------------------------------
    # Изображения
    # --------------------------------------------------------------------------
    def _add_images(self):
        current_count = len(self.image_widgets)
        max_new = 3 - current_count
        if max_new <= 0:
            QMessageBox.warning(self, "Лимит", "Максимум 3 изображения для одной детали.")
            return
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Выберите локальные изображения (до 3)", "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if not file_paths:
            return
        file_paths = file_paths[:max_new]
        for fp in file_paths:
            self._add_image_widget(fp)

    def _add_image_widget(self, file_path):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
            }
            QFrame:hover {
                border: 1px solid #3399ff;
                background-color: #f0f8ff;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        # Превью изображения
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        img_label = QLabel()
        if not pixmap.isNull():
            img_label.setPixmap(pixmap)
        else:
            img_label.setText("⚠️")
            img_label.setStyleSheet("font-size: 24pt;")
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setFixedSize(100, 100)
        img_label.setStyleSheet("background-color: #ffffff; border-radius: 4px;")
        layout.addWidget(img_label, alignment=Qt.AlignCenter)

        # Имя файла
        name_label = QLabel(Path(file_path).name)
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 9pt; color: #333; padding: 2px;")
        name_label.setMaximumHeight(30)
        layout.addWidget(name_label)

        # Кнопка удаления с текстом
        del_btn = QPushButton("Удалить")
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 9pt;
            }
            QPushButton:hover { background-color: #ff5252; }
            QPushButton:pressed { background-color: #ff3838; }
        """)
        del_btn.setFixedHeight(22)
        del_btn.clicked.connect(lambda: self._remove_image_widget(frame))
        
        overlay_layout = QHBoxLayout()
        overlay_layout.addStretch()
        overlay_layout.addWidget(del_btn)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(overlay_layout)

        self.img_container_layout.addWidget(frame)
        self.image_widgets.append((frame, file_path))

    def _remove_image_widget(self, frame):
        for i, (f, path) in enumerate(self.image_widgets):
            if f == frame:
                self.image_widgets.pop(i)
                frame.deleteLater()
                break

    def _get_image_paths(self):
        return [path for _, path in self.image_widgets]

    # --------------------------------------------------------------------------
    # Прочее: комбобоксы, категории, номинал, места и т.д.
    # --------------------------------------------------------------------------
    def _load_comboboxes(self):
        part_types = set(self.db.get_dictionary_values('part_type'))
        for part in self.db.get_all_parts_filtered():
            pt = part.get('part_type')
            if pt:
                part_types.add(pt)
        self.part_type_combo.clear()
        self.part_type_combo.addItems(sorted(part_types))

        manufacturers = set(self.db.get_dictionary_values('manufacturer'))
        for part in self.db.get_all_parts_filtered():
            m = part.get('manufacturer')
            if m:
                manufacturers.add(m)
        self.manufacturer_combo.clear()
        self.manufacturer_combo.addItems(sorted(manufacturers))

    def _open_category_selector(self):
        dialog = CategorySelectorDialog(
            self, db=self.db,
            selected_category=self.category_edit.text(),
            start_depth=self.start_depth
        )
        dialog.category_selected.connect(self._on_category_selected)
        dialog.exec()

    def _on_category_selected(self, category_path):
        self.category_edit.setText(category_path)
        self._update_units_by_category(category_path)
        self._show_dims_for_capacitor(category_path)

    def _update_units_by_category(self, category_path):
        path_lower = category_path.lower()
        if "конденсатор" in path_lower:
            units = ["", "пФ", "нФ", "мкФ", "Ф"]
        elif "резистор" in path_lower:
            units = ["", "Ом", "кОм", "МОм"]
        else:
            units = ["", "Ом", "кОм", "МОм", "пФ", "нФ", "мкФ", "Ф",
                     "Гн", "мГн", "мкГн", "В", "А", "мА"]
        combo = self.unit_combo
        current = combo.currentText()
        combo.clear()
        combo.addItems(units)
        if current in units:
            combo.setCurrentText(current)
        else:
            combo.setCurrentIndex(0)

    def _show_dims_for_capacitor(self, category_path):
        """Автоматически показывает/скрывает группу габаритов в зависимости от категории."""
        if category_path and 'конденсатор' in category_path.lower():
            self.dims_group.setVisible(True)
        else:
            self.dims_group.setVisible(False)

    def _parse_and_normalize(self, raw_text: str):
        if not raw_text:
            return None, "", ""
        text = raw_text.strip()
        match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Zμµ]?[a-zA-Z]*)$", text)
        if not match:
            try:
                num = float(text)
                if num.is_integer():
                    num = int(num)
                return num, "", str(num)
            except Exception:
                return None, "", ""
        num_str, unit_raw = match.groups()
        try:
            numeric = float(num_str)
            if numeric.is_integer():
                numeric = int(numeric)
        except Exception:
            return None, "", ""
        unit_lower = unit_raw.lower()
        unit_map = {
            'k': 'кОм', 'm': 'МОм', 'r': 'Ом', 'ohm': 'Ом',
            'n': 'нФ', 'u': 'мкФ', 'p': 'пФ', 'mf': 'мкФ',
            'µ': 'мкФ', 'μ': 'мкФ',
            'mhz': 'МГц', 'khz': 'кГц', 'hz': 'Гц',
            'v': 'В', 'mv': 'мВ', 'a': 'А', 'ma': 'мА',
            'h': 'Гн', 'mh': 'мГн'
        }
        unit_full = unit_map.get(unit_lower, unit_raw.upper())
        normalized = f"{numeric}{unit_full}" if unit_full else str(numeric)
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

    def _assemble_name(self):
        category_path = self.category_edit.text().strip()
        voltage = power = ''
        if category_path:
            last_part = category_path.split('/')[-1].strip()
            if re.search(r'\d+V', last_part, re.IGNORECASE):
                voltage = last_part.replace('V', 'В').replace('v', 'В')
            else:
                match = re.search(r'([\d\.]+)\s*[WВт]', last_part, re.IGNORECASE)
                if match:
                    power = f"{match.group(1)} Вт"
        
        raw_value = self.value_edit.text().strip()
        numeric, unit, normalized = self._parse_and_normalize(raw_value)
        if not unit and self.unit_combo.currentText():
            unit = self.unit_combo.currentText()
            if numeric is not None:
                normalized = f"{numeric}{unit}"
            else:
                normalized = unit
                
        if unit:
            value_part = normalized
        elif numeric is not None:
            value_part = str(numeric)
        else:
            value_part = raw_value
        
        package = self.package_combo.currentText().strip()
        name_parts = [p for p in (value_part, voltage, power, package) if p]
        assembled = " ".join(name_parts)
        
        if assembled:
            self.name_edit.setText(assembled)
        else:
            QMessageBox.information(
                self, "Невозможно собрать",
                "Заполните хотя бы номинал или выберите категорию с параметрами"
            )

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
            path = self._build_category_path(cat_id, cats)
            self.category_edit.setText(path)
            self._update_units_by_category(path)
            self._show_dims_for_capacitor(path)
        else:
            self.category_edit.setText("")

        pt_val = data.get('part_type', '')
        idx = self.part_type_combo.findText(pt_val)
        self.part_type_combo.setCurrentIndex(idx) if idx >= 0 else self.part_type_combo.setCurrentText(pt_val)

        m_val = data.get('manufacturer', '')
        idx = self.manufacturer_combo.findText(m_val)
        self.manufacturer_combo.setCurrentIndex(idx) if idx >= 0 else self.manufacturer_combo.setCurrentText(m_val)

        self.part_number_edit.setText(data.get('part_number', ''))
        self.package_combo.setCurrentText(data.get('package', ''))
        self.quantity_spin.setValue(data.get('quantity', 0))
        self.price_spin.setValue(data.get('price', 0))
        self.diameter_spin.setValue(data.get('diameter_mm', 0) or 0)
        self.height_spin.setValue(data.get('height_mm', 0) or 0)
        self.lead_pitch_spin.setValue(data.get('lead_pitch_mm', 0) or 0)
        self.lead_diameter_spin.setValue(data.get('lead_diameter_mm', 0) or 0)

        # Номинал и единица
        value_numeric = data.get('value_numeric')
        value_unit = data.get('value_unit', '')
        if value_numeric is not None:
            if isinstance(value_numeric, float) and value_numeric.is_integer():
                self.value_edit.setText(str(int(value_numeric)))
            else:
                self.value_edit.setText(str(value_numeric))
        else:
            self.value_edit.setText("")
        if value_unit:
            idx = self.unit_combo.findText(value_unit)
            if idx >= 0:
                self.unit_combo.setCurrentIndex(idx)
            else:
                self.unit_combo.addItem(value_unit)
                self.unit_combo.setCurrentText(value_unit)
        else:
            self.unit_combo.setCurrentIndex(0)

        # Статус
        status_val = data.get('status', 'Новое')
        for i in range(self.status_combo.count()):
            if self.status_combo.itemText(i) == status_val:
                self.status_combo.setCurrentIndex(i)
                break

        # Место хранения
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

        # Изображения (только локальные файлы)
        image_paths = [
            data.get('image_path', ''),
            data.get('image_path_2', ''),
            data.get('image_path_3', '')
        ]
        for path in image_paths:
            if path and not path.startswith(('http://', 'https://')):
                full_path = DATA_DIR / "images" / Path(path).name
                if full_path.exists():
                    self._add_image_widget(str(full_path))

        # Даташит
        self.datasheet_path_edit.setText(data.get('datasheet_path', ''))

        # Дата ревизии
        if data.get('revision_date'):
            q_date = QDate.fromString(data['revision_date'], "yyyy-MM-dd")
            if q_date.isValid():
                self.revision_date.setDate(q_date)

        # Заметки
        self.notes_edit.setPlainText(data.get('notes', ''))

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "⚠️ Наименование обязательно!")
            return
        part_type = self.part_type_combo.currentText().strip()
        if part_type:
            self.db.add_dictionary_value('part_type', part_type)
        manufacturer = self.manufacturer_combo.currentText().strip()
        if manufacturer:
            self.db.add_dictionary_value('manufacturer', manufacturer)
        self.accept()

    def get_location_string(self):
        return ' / '.join([p.strip() for p in [
            self.location_place_combo.currentText(),
            self.location_container_combo.currentText(),
            self.location_shelf_combo.currentText(),
            self.location_section_combo.currentText()
        ] if p.strip()])

    def get_data(self):
        category_path = self.category_edit.text().strip()
        category_id = self._get_category_id_from_path(category_path) if category_path else None
        raw_value = self.value_edit.text().strip()
        numeric, unit, normalized = self._parse_and_normalize(raw_value)
        if not unit and self.unit_combo.currentText():
            unit = self.unit_combo.currentText()
            if numeric is None:
                match = re.search(r"([0-9]+(?:\.[0-9]+)?)", raw_value)
                if match:
                    numeric = float(match.group(1))
                    if numeric.is_integer():
                        numeric = int(numeric)
        value_raw = raw_value if raw_value else None

        return {
            'name': self.name_edit.text().strip(),
            'category_id': category_id,
            'part_type': self.part_type_combo.currentText().strip(),
            'package': self.package_combo.currentText(),
            'manufacturer': self.manufacturer_combo.currentText().strip(),
            'part_number': self.part_number_edit.text().strip(),
            'quantity': self.quantity_spin.value(),
            'price': self.price_spin.value(),
            'location': self.get_location_string(),
            'status': self.status_combo.currentText(),
            'datasheet_path': self.datasheet_path_edit.text().strip(),
            'revision_date': self.revision_date.date().toString("yyyy-MM-dd") if self.revision_date.date().isValid() else None,
            'notes': self.notes_edit.toPlainText().strip(),
            'value_numeric': numeric,
            'value_unit': unit if unit else None,
            'value_raw': value_raw,
            'diameter_mm': self.diameter_spin.value() if self.diameter_spin.value() > 0 else None,
            'height_mm': self.height_spin.value() if self.height_spin.value() > 0 else None,
            'lead_pitch_mm': self.lead_pitch_spin.value() if self.lead_pitch_spin.value() > 0 else None,
            'lead_diameter_mm': self.lead_diameter_spin.value() if self.lead_diameter_spin.value() > 0 else None,
            'image_files': self._get_image_paths()
        }