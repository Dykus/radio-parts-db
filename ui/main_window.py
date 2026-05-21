# ui/main_window.py
import os
import logging
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QTableView, QHeaderView, QPushButton, QLineEdit,
    QStatusBar, QLabel, QDialog, QFormLayout, QComboBox, 
    QSpinBox, QDoubleSpinBox, QDateTimeEdit, QTextEdit,
    QDialogButtonBox, QAbstractItemView, QMessageBox, QFileDialog,
    QScrollArea, QTreeWidget, QTreeWidgetItem, QStyle, QSizePolicy
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression, QSize, QDate, QRect
from PySide6.QtGui import QColor, QStandardItemModel, QStandardItem, QRegularExpressionValidator, QPixmap, QIcon

logger = logging.getLogger(__name__)

from core.database import Database
from utils.importer import import_csv

# Файл для сохранения настроек окна
SETTINGS_FILE = "window_settings.json"

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
        
        self.manufacturer_edit = QLineEdit()
        self.part_number_edit = QLineEdit()
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 999999)
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("₽ ")
        
        # === ТРЕХУРОВНЕВОЕ МЕСТО ХРАНЕНИЯ ===
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
        self.location_container_combo.currentTextChanged.connect(self._update_location_cells)
        
        self.location_cell_combo = QComboBox()
        self.location_cell_combo.setEditable(True)
        self.location_cell_combo.setPlaceholderText("Ячейка")
        self.location_cell_combo.setMinimumWidth(100)
        
        location_layout.addWidget(self.location_place_combo)
        location_layout.addWidget(self.location_container_combo)
        location_layout.addWidget(self.location_cell_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["new", "used", "suspect", "broken"])
        self.status_combo.setCurrentText("new")
        
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
        layout.addRow("Производитель", self.manufacturer_edit)
        layout.addRow("Артикул", self.part_number_edit)
        
        qty_price = QHBoxLayout()
        qty_price.addWidget(self.quantity_spin)
        qty_price.addWidget(self.price_spin)
        layout.addRow("Кол-во / Цена", qty_price)
        
        layout.addRow("📍 Место хранения", location_widget)
        layout.addRow("Статус", self.status_combo)
        
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
        self.location_cell_combo.clear()
        if not place: return
        
        if self.db:
            containers = set()
            parts = self.db.get_all_parts_filtered()
            for part in parts:
                location = part.get('location', '')
                if location:
                    p = [x.strip() for x in location.split('/')]
                    if len(p) >= 2 and p[0] == place:
                        containers.add(p[1])
            self.location_container_combo.addItems([""] + sorted(containers))
    
    def _update_location_cells(self, container):
        self.location_cell_combo.clear()
        place = self.location_place_combo.currentText()
        if not place or not container: return
        
        if self.db:
            cells = set()
            parts = self.db.get_all_parts_filtered()
            for part in parts:
                location = part.get('location', '')
                if location:
                    p = [x.strip() for x in location.split('/')]
                    if len(p) >= 3 and p[0] == place and p[1] == container:
                        cells.add(p[2])
            self.location_cell_combo.addItems([""] + sorted(cells))
    
    def _fill_form(self, data):
        self.name_edit.setText(data.get('name', ''))
        self.part_type_edit.setText(data.get('part_type', ''))
        self.package_combo.setCurrentText(data.get('package', ''))
        self.manufacturer_edit.setText(data.get('manufacturer', ''))
        self.part_number_edit.setText(data.get('part_number', ''))
        self.quantity_spin.setValue(data.get('quantity', 0))
        self.price_spin.setValue(data.get('price', 0))
        
        location = data.get('location', '')
        if location:
            parts = [p.strip() for p in location.split('/')]
            if len(parts) >= 1:
                self.location_place_combo.setCurrentText(parts[0])
                self._update_location_containers(parts[0])
            if len(parts) >= 2:
                self.location_container_combo.setCurrentText(parts[1])
                self._update_location_cells(parts[0])
            if len(parts) >= 3:
                self.location_cell_combo.setCurrentText(parts[2])
        
        self.status_combo.setCurrentText(data.get('status', 'new'))
        self.image_path_edit.setText(data.get('image_path', ''))
        self.datasheet_path_edit.setText(data.get('datasheet_path', ''))
        
        rev_date_str = data.get('revision_date')
        if rev_date_str:
            q_date = QDate.fromString(rev_date_str, "yyyy-MM-dd")
            if q_date.isValid():
                self.revision_date.setDate(q_date)
    
    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "⚠️ Наименование обязательно!")
            return
        self.accept()
    
    def get_location_string(self):
        place = self.location_place_combo.currentText().strip()
        container = self.location_container_combo.currentText().strip()
        cell = self.location_cell_combo.currentText().strip()
        parts = [p for p in [place, container, cell] if p]
        return ' / '.join(parts) if parts else ''
    
    def get_data(self):
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
            'status': self.status_combo.currentText(),
            'image_path': self.image_path_edit.text().strip(),
            'datasheet_path': self.datasheet_path_edit.text().strip(),
            'revision_date': self.revision_date.date().toString("yyyy-MM-dd") if self.revision_date.date().isValid() else None,
            'notes': self.notes_edit.toPlainText().strip()
        }


class PartsTableModel(QStandardItemModel):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setHorizontalHeaderLabels(["ID", "Наименование", "Тип", "Корпус", "Кол-во", "Цена", "Место", "Статус"])
        self.load_data()
    
    def load_data(self, category_id=None, filter_type="all", location_path=None):
        self.removeRows(0, self.rowCount())
        parts = self.db.get_all_parts_filtered(category_id, filter_type, location_path)
        for p in parts:
            items = [
                QStandardItem(str(p['id'])), QStandardItem(p['name']),
                QStandardItem(p['part_type'] or ''), QStandardItem(p['package'] or ''),
                QStandardItem(str(p['quantity'])), QStandardItem(f"{p['price']:.2f}"),
                QStandardItem(p['location'] or ''), QStandardItem(p['status'] or 'new')
            ]
            qty, status = p['quantity'], p['status']
            if status == 'broken' or qty == 0:
                bg, fg = QColor("#ffcdd2"), QColor("#000000")
            elif qty < 10:
                bg, fg = QColor("#fff9c4"), QColor("#000000")
            else:
                bg, fg = QColor("#c8e6c9"), QColor("#000000")
            for item in items:
                item.setBackground(bg)
                item.setForeground(fg)
                item.setEditable(False)
            self.appendRow(items)


class PartsFilterProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterKeyColumn(-1)
    def set_search_text(self, text):
        rx = QRegularExpression(QRegularExpression.escape(text), QRegularExpression.CaseInsensitiveOption)
        self.setFilterRegularExpression(rx)


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle("📦 RadioPartsDB v0.6.1")
        self.setMinimumSize(1200, 700)
        self.current_filter = "all"
        self.selected_location_path = None
        
        # Загрузка настроек окна
        self._load_window_settings()
        
        self._init_ui()
        self._load_categories()
        self._load_locations()
    
    def _load_window_settings(self):
        """Загружает позицию и размер окна из файла."""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    geom = settings.get('geometry')
                    if geom:
                        self.setGeometry(QRect(*geom))
            except Exception as e:
                logger.warning(f"Не удалось загрузить настройки окна: {e}")

    def _save_window_settings(self):
        """Сохраняет позицию и размер окна в файл."""
        try:
            geom = self.geometry()
            settings = {
                'geometry': [geom.x(), geom.y(), geom.width(), geom.height()]
            }
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            logger.warning(f"Не удалось сохранить настройки окна: {e}")

    def closeEvent(self, event):
        """Вызывается при закрытии окна."""
        self._save_window_settings()
        super().closeEvent(event)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self._add_part)
        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.clicked.connect(self._edit_part)
        self.del_btn = QPushButton("🗑️ Удалить")
        self.del_btn.clicked.connect(self._delete_part)
        self.import_btn = QPushButton("📥 Импорт CSV")
        self.import_btn.clicked.connect(self._import_csv)
        
        self.filter_all_btn = QPushButton("📋 Все")
        self.filter_all_btn.setCheckable(True)
        self.filter_all_btn.setChecked(True)
        self.filter_all_btn.clicked.connect(lambda: self._apply_filter("all"))
        
        self.filter_stock_btn = QPushButton("✅ В наличии")
        self.filter_stock_btn.setCheckable(True)
        self.filter_stock_btn.clicked.connect(lambda: self._apply_filter("in_stock"))
        
        self.filter_low_btn = QPushButton("⚠️ Мало (<10)")
        self.filter_low_btn.setCheckable(True)
        self.filter_low_btn.clicked.connect(lambda: self._apply_filter("low_stock"))
        
        self.filter_out_btn = QPushButton("❌ Нет на складе")
        self.filter_out_btn.setCheckable(True)
        self.filter_out_btn.clicked.connect(lambda: self._apply_filter("out_of_stock"))
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск...")
        self.search_edit.textChanged.connect(self._filter_table)
        
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.del_btn)
        toolbar.addWidget(self.import_btn)
        toolbar.addWidget(QLabel("|"))
        toolbar.addWidget(self.filter_all_btn)
        toolbar.addWidget(self.filter_stock_btn)
        toolbar.addWidget(self.filter_low_btn)
        toolbar.addWidget(self.filter_out_btn)
        toolbar.addStretch()
        toolbar.addWidget(self.search_edit)
        main_layout.addLayout(toolbar)
        
        main_splitter = QSplitter(Qt.Horizontal)
        
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(["Категории"])
        self.tree_view.setModel(self.tree_model)
        self.tree_view.clicked.connect(self._on_category_click)
        self.tree_view.setMaximumWidth(250)
        main_splitter.addWidget(self.tree_view)
        
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.parts_model = PartsTableModel(self.db)
        self.filter_model = PartsFilterProxyModel()
        self.filter_model.setSourceModel(self.parts_model)
        
        self.parts_table = QTableView()
        self.parts_table.setModel(self.filter_model)
        self.parts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.parts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.parts_table.doubleClicked.connect(self._edit_part)
        self.parts_table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        
        table_layout.addWidget(self.parts_table)
        main_splitter.addWidget(table_widget)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        photo_label = QLabel("🖼️ Предпросмотр")
        photo_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #555;") # ✅ Исправлен цвет текста
        right_layout.addWidget(photo_label)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(200)
        # ✅ Исправлены цвета на нейтральные/системные
        self.image_label.setStyleSheet("""
            QLabel { 
                background-color: #f0f0f0; 
                border: 1px solid #ccc; 
                border-radius: 3px; 
                color: #888; 
            }
        """)
        self.image_label.setText("")
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.image_label)
        right_layout.addWidget(scroll_area)
        
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #333; padding: 5px; font-size: 11px;") # ✅ Исправлен цвет текста
        right_layout.addWidget(self.info_label)

        location_label = QLabel("📍 Навигатор по местам")
        location_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #555; margin-top: 10px;") # ✅ Исправлен цвет текста
        right_layout.addWidget(location_label)
        
        self.location_tree = QTreeWidget()
        self.location_tree.setHeaderHidden(True)
        # ✅ Исправлены стили дерева под светлую тему
        self.location_tree.setStyleSheet("""
            QTreeWidget { 
                background-color: #ffffff; 
                border: 1px solid #ccc; 
                color: #000000; 
            }
            QTreeWidget::item:hover { background-color: #e5f3ff; }
            QTreeWidget::item:selected { background-color: #0078d7; color: white; }
        """)
        self.location_tree.itemClicked.connect(self._on_location_click)
        right_layout.addWidget(self.location_tree)
        
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([250, 700, 300])
        
        main_layout.addWidget(main_splitter)
        
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._update_status()

    def _apply_filter(self, filter_type):
        self.current_filter = filter_type
        self.filter_all_btn.setChecked(False)
        self.filter_stock_btn.setChecked(False)
        self.filter_low_btn.setChecked(False)
        self.filter_out_btn.setChecked(False)
        
        if filter_type == "all": self.filter_all_btn.setChecked(True)
        elif filter_type == "in_stock": self.filter_stock_btn.setChecked(True)
        elif filter_type == "low_stock": self.filter_low_btn.setChecked(True)
        elif filter_type == "out_of_stock": self.filter_out_btn.setChecked(True)
        
        self._refresh_table()
        self._update_status()
    
    def _get_selected_category(self):
        indexes = self.tree_view.selectionModel().selectedIndexes()
        if indexes:
            return self.tree_model.data(indexes[0], Qt.UserRole)
        return None
    
    def _on_selection_changed(self, selected, deselected):
        indexes = self.parts_table.selectionModel().selectedRows()
        if not indexes:
            self._clear_image_preview()
            self.location_tree.clearSelection()
            return
        
        row = indexes[0].row()
        part_id = int(self.filter_model.data(self.filter_model.index(row, 0)))
        part = self.db.get_part(part_id)
        
        if part:
            self._show_image_preview(part)
            self._highlight_location_in_tree(part.get('location', ''))
        else:
            self._clear_image_preview()
            self.location_tree.clearSelection()

    def _highlight_location_in_tree(self, location_path):
        if not location_path or not location_path.strip():
            self.location_tree.clearSelection()
            return

        parts = [p.strip() for p in location_path.split('/') if p.strip()]
        if not parts:
            self.location_tree.clearSelection()
            return

        root = self.location_tree.topLevelItem(0)
        if not root:
            return

        current_item = root
        for target_name in parts:
            found = False
            for i in range(current_item.childCount()):
                child = current_item.child(i)
                child_text = child.text(0).strip()
                if child_text == target_name:
                    current_item = child
                    current_item.setExpanded(True)
                    found = True
                    break
            if not found:
                self.location_tree.clearSelection()
                return

        self.location_tree.setCurrentItem(current_item)
        self.location_tree.scrollToItem(current_item, QAbstractItemView.PositionAtCenter)

    def _show_image_preview(self, part):
        image_path = part.get('image_path', '').strip()
        if not image_path:
            self._clear_image_preview()
            return
        
        pixmap = QPixmap()
        if ',' in image_path:
            urls = [url.strip() for url in image_path.split(',')]
        else:
            urls = [image_path]
        
        for img_source in urls:
            img_source = img_source.strip()
            if not img_source: continue
            try:
                if img_source.startswith('file://'): continue
                elif img_source.startswith(('http://', 'https://')):
                    import urllib.request, ssl
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    req = urllib.request.Request(img_source, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                        image_data = response.read()
                    if image_data and pixmap.loadFromData(image_data):
                        logger.info(f"✅ Загружено изображение из {img_source[:50]}...")
                        break
                    else: continue
                else:
                    if os.path.exists(img_source):
                        if pixmap.load(img_source):
                            logger.info(f"✅ Загружен локальный файл: {img_source}")
                            break
            except Exception: continue
        
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(self.image_label.size() - QSize(20, 20), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setText("")
            # ✅ Цвет фона картинки при загрузке остается нейтральным
            self.image_label.setStyleSheet("QLabel { background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 3px; padding: 5px; }")
        else:
            self._clear_image_preview()
            return
        
        info_text = f"<b>{part['name']}</b><br>"
        if part.get('part_type'): info_text += f"Тип: {part['part_type']}<br>"
        if part.get('package'): info_text += f"Корпус: {part['package']}<br>"
        info_text += f"Кол-во: {part['quantity']}<br>Цена: {part['price']:.2f} ₽"
        self.info_label.setText(info_text)
    
    def _clear_image_preview(self):
        self.image_label.setText("📷")
        # ✅ Возвращаем нейтральный стиль заглушки
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 3px; color: #888;")
        self.image_label.setPixmap(QPixmap())
        self.info_label.setText("")
    
    def _load_categories(self):
        self.tree_model.clear()
        self.tree_model.setHorizontalHeaderLabels(["Категории"])
        root_item = self.tree_model.invisibleRootItem()
        categories = self.db.get_categories()
        item_map = {}
        for cat in categories:
            cat_id, name, parent_id = cat
            item = QStandardItem(name)
            item.setData(cat_id, Qt.UserRole)
            item_map[cat_id] = item
        for cat in categories:
            cat_id, name, parent_id = cat
            item = item_map[cat_id]
            if parent_id is None or parent_id == 0:
                root_item.appendRow(item)
            else:
                parent_item = item_map.get(parent_id)
                if parent_item: parent_item.appendRow(item)
                else: root_item.appendRow(item)

    def _on_category_click(self, index):
        cat_id = self.tree_model.data(index, Qt.UserRole)
        self.parts_model.load_data(cat_id, self.current_filter, self.selected_location_path)
        self._update_status()

    def _filter_table(self, text):
        self.filter_model.set_search_text(text)
    
    def _load_locations(self):
        self.location_tree.clear()
        location_data = self.db.get_location_tree()
        
        def build_tree(data_dict, parent_item):
            for key, value in sorted(data_dict.items()):
                item = QTreeWidgetItem(parent_item, [key])
                item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
                build_tree(value, item)

        root = QTreeWidgetItem(self.location_tree, ["🏠 Все места"])
        root.setIcon(0, self.style().standardIcon(QStyle.SP_DriveHDIcon))
        build_tree(location_data, root)
        self.location_tree.expandAll()

    def _on_location_click(self, item, column):
        path_parts = []
        current = item
        while current:
            text = current.text(0).strip()
            text = text.replace("🏠", "").replace("📂", "").replace("📄", "").strip()
            path_parts.append(text)
            current = current.parent()
        
        full_path = " / ".join(reversed(path_parts))
        
        if full_path.startswith("Все места / "):
            full_path = full_path[len("Все места / "):]
        elif full_path == "Все места":
            full_path = None
            
        self.selected_location_path = full_path
        self._refresh_table()
        self._update_status()

    def _refresh_table(self):
        category_id = self._get_selected_category()
        self.parts_model.load_data(category_id, self.current_filter, self.selected_location_path)

    def _update_status(self):
        stats = self.db.get_stats()
        loc_text = self.selected_location_path if self.selected_location_path else "Везде"
        self.status.showMessage(f"📦 Всего: {stats['total_parts']} | 💰 {stats['total_value']:.0f}₽ | 📍 Место: {loc_text}")

    def _add_part(self):
        dialog = PartDialog(self, db=self.db)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            cat_name = data['category']
            if cat_name:
                cats = self.db.get_categories()
                cat_id = next((c[0] for c in cats if c[1] == cat_name), None)
                if cat_id is None: cat_id = self.db.create_category(cat_name)
                data['category_id'] = cat_id
            self.db.create_part(data)
            
            self._load_locations()
            
            self._refresh_table()
            self._load_categories()
            QMessageBox.information(self, "✅ Успех", "Компонент добавлен!")
    
    def _edit_part(self):
        indexes = self.parts_table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "⚠️ Внимание", "Выберите компонент для редактирования")
            return
        row = indexes[0].row()
        part_id = int(self.filter_model.data(self.filter_model.index(row, 0)))
        part = self.db.get_part(part_id)
        if part:
            dialog = PartDialog(self, part_data=part, db=self.db)
            if dialog.exec() == QDialog.Accepted:
                self.db.update_part(part_id, dialog.get_data())
                
                self._load_locations()
                
                self._refresh_table()
                self._load_categories()
                self._update_status()
                QMessageBox.information(self, "✅ Успех", "Компонент обновлён!")
    
    def _delete_part(self):
        indexes = self.parts_table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "⚠️ Внимание", "Выберите компонент для удаления")
            return
        row = indexes[0].row()
        part_id = int(self.filter_model.data(self.filter_model.index(row, 0)))
        part_name = self.filter_model.data(self.filter_model.index(row, 1))
        if QMessageBox.question(self, "❓ Подтверждение", f"Удалить \"{part_name}\"?\n\nДанные будут перемещены в архив.", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete_part(part_id)
            self._refresh_table()
            self._load_categories()
            self._update_status()
            QMessageBox.information(self, "✅ Успех", "Компонент удалён и архивирован")

    def _import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Импорт из CSV", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            if QMessageBox.question(self, "Подтверждение", "Начать импорт данных из CSV файла?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                try:
                    self.status.showMessage("⏳ Идет импорт...")
                    QApplication.processEvents()
                    imported, errors = import_csv(self.db, file_path)
                    self._refresh_table()
                    self._load_categories()
                    self._load_locations()
                    self._update_status()
                    QMessageBox.information(self, "Результат", f"✅ Импорт завершен!\nДобавлено: {imported}\nОшибок: {errors}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка импорта", str(e))