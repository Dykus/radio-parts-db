# ui/main_window.py
import os
import logging
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QTableView, QHeaderView, QPushButton, QLineEdit,
    QStatusBar, QLabel, QDialog, QFormLayout, QComboBox, 
    QSpinBox, QDoubleSpinBox, QDateTimeEdit, QTextEdit,
    QDialogButtonBox, QAbstractItemView, QMessageBox, QFileDialog,
    QScrollArea
)
# ✅ ИСПРАВЛЕНО: QDate перенесён в QtCore
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression, QSize, QDate
from PySide6.QtGui import QColor, QStandardItemModel, QStandardItem, QRegularExpressionValidator, QPixmap, QIcon

logger = logging.getLogger(__name__)

from core.database import Database
from utils.importer import import_csv


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
        
        self.location_combo = QComboBox()
        self.location_combo.setEditable(True)
        self.location_combo.addItems(["Ящик 1", "Ящик 2", "Полка А", "Полка Б", "Коробка"])
        
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
        
        layout.addRow("Место хранения", self.location_combo)
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
    
    def _fill_form(self, data):
        self.name_edit.setText(data.get('name', ''))
        self.part_type_edit.setText(data.get('part_type', ''))
        self.package_combo.setCurrentText(data.get('package', ''))
        self.manufacturer_edit.setText(data.get('manufacturer', ''))
        self.part_number_edit.setText(data.get('part_number', ''))
        self.quantity_spin.setValue(data.get('quantity', 0))
        self.price_spin.setValue(data.get('price', 0))
        self.location_combo.setCurrentText(data.get('location', ''))
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
            'location': self.location_combo.currentText(),
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
    
    def load_data(self, category_id=None, filter_type="all"):
        self.removeRows(0, self.rowCount())
        parts = self.db.get_all_parts_filtered(category_id, filter_type)
        for p in parts:
            items = [
                QStandardItem(str(p['id'])), QStandardItem(p['name']),
                QStandardItem(p['part_type'] or ''), QStandardItem(p['package'] or ''),
                QStandardItem(str(p['quantity'])), QStandardItem(f"{p['price']:.2f}"),
                QStandardItem(p['location'] or ''), QStandardItem(p['status'] or 'new')
            ]
            qty, status = p['quantity'], p['status']
            if status == 'broken' or qty == 0: bg, fg = QColor("#ffcdd2"), QColor("#000000")
            elif qty < 10: bg, fg = QColor("#fff9c4"), QColor("#000000")
            else: bg, fg = QColor("#c8e6c9"), QColor("#000000")
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
        self.setWindowTitle("📦 RadioPartsDB v0.4.0")
        self.setMinimumSize(1400, 700)
        self.current_filter = "all"
        self._init_ui()
        self._load_categories()
    
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # === ПАНЕЛЬ ИНСТРУМЕНТОВ ===
        toolbar = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self._add_part)
        
        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.clicked.connect(self._edit_part)
        
        self.del_btn = QPushButton("🗑️ Удалить")
        self.del_btn.clicked.connect(self._delete_part)
        
        self.import_btn = QPushButton("📥 Импорт CSV")
        self.import_btn.clicked.connect(self._import_csv)
        
        # === БЫСТРЫЕ ФИЛЬТРЫ ===
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
        
        # Собираем тулбар
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
        
        # === ОСНОВНОЙ РАЗДЕЛИТЕЛЬ (Дерево + Таблица + Фото) ===
        main_splitter = QSplitter(Qt.Horizontal)
        
        # ЛЕВАЯ ПАНЕЛЬ: Дерево категорий
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(["Категории"])
        self.tree_view.setModel(self.tree_model)
        self.tree_view.clicked.connect(self._on_category_click)
        self.tree_view.setMaximumWidth(250)
        
        main_splitter.addWidget(self.tree_view)
        
        # ЦЕНТРАЛЬНАЯ ПАНЕЛЬ: Таблица
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
        
        # ПРАВАЯ ПАНЕЛЬ: Предпросмотр фото
        photo_panel = QWidget()
        photo_layout = QVBoxLayout(photo_panel)
        photo_layout.setContentsMargins(10, 10, 10, 10)
        
        photo_label = QLabel("🖼️ Предпросмотр")
        photo_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        photo_layout.addWidget(photo_label)
        
        # Область для изображения
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px dashed #555;
                border-radius: 5px;
                color: #888;
            }
        """)
        self.image_label.setText("📷\nИзображение\nне выбрано")
        self.image_label.setMinimumSize(300, 300)
        
        # Прокрутка для больших изображений
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.image_label)
        scroll_area.setMinimumWidth(300)
        
        photo_layout.addWidget(scroll_area)
        
        # Информация о компоненте
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #aaa; padding: 5px;")
        photo_layout.addWidget(self.info_label)
        
        photo_layout.addStretch()
        
        main_splitter.addWidget(photo_panel)
        main_splitter.setSizes([250, 700, 300])
        
        main_layout.addWidget(main_splitter)
        
        # Статус-бар
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._update_status()
    
    def _apply_filter(self, filter_type):
        """Применение быстрого фильтра."""
        self.current_filter = filter_type
        
        # Сбрасываем все кнопки
        self.filter_all_btn.setChecked(False)
        self.filter_stock_btn.setChecked(False)
        self.filter_low_btn.setChecked(False)
        self.filter_out_btn.setChecked(False)
        
        # Активируем нужную
        if filter_type == "all":
            self.filter_all_btn.setChecked(True)
        elif filter_type == "in_stock":
            self.filter_stock_btn.setChecked(True)
        elif filter_type == "low_stock":
            self.filter_low_btn.setChecked(True)
        elif filter_type == "out_of_stock":
            self.filter_out_btn.setChecked(True)
        
        # Перезагружаем таблицу
        category_id = self._get_selected_category()
        self.parts_model.load_data(category_id, filter_type)
        self._update_status()
    
    def _get_selected_category(self):
        """Получить ID выбранной категории."""
        indexes = self.tree_view.selectionModel().selectedIndexes()
        if indexes:
            return self.tree_model.data(indexes[0], Qt.UserRole)
        return None
    
    def _on_selection_changed(self, selected, deselected):
        """Обработка изменения выделения в таблице."""
        indexes = self.parts_table.selectionModel().selectedRows()
        if not indexes:
            self._clear_image_preview()
            return
        
        row = indexes[0].row()
        part_id = int(self.filter_model.data(self.filter_model.index(row, 0)))
        part = self.db.get_part(part_id)
        
        if part:
            self._show_image_preview(part)
        else:
            self._clear_image_preview()
    
    def _show_image_preview(self, part):
        """Показать изображение компонента (локальное или из интернета)."""
        image_path = part.get('image_path', '').strip()
        
        if not image_path:
            self._clear_image_preview()
            return
        
        pixmap = QPixmap()
        
        # Проверяем, это несколько URL через запятую
        if ',' in image_path:
            urls = [url.strip() for url in image_path.split(',')]
        else:
            urls = [image_path]
        
        # Пробуем загрузить каждое изображение по очереди
        for img_source in urls:
            img_source = img_source.strip()
            if not img_source:
                continue
                
            try:
                # Локальный файл
                if img_source.startswith('file://'):
                    # Android пути не будут работать на ПК
                    continue
                elif img_source.startswith(('http://', 'https://')):
                    # === ЗАГРУЗКА ИЗ ИНТЕРНЕТА ===
                    import urllib.request
                    import ssl
                    
                    # Игнорируем ошибки SSL
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    
                    # Загружаем данные с таймаутом
                    req = urllib.request.Request(
                        img_source,
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    )
                    with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                        image_data = response.read()
                    
                    # Пробуем загрузить в QPixmap
                    if image_data and pixmap.loadFromData(image_data):
                        logger.info(f"✅ Загружено изображение из {img_source[:50]}...")
                        break  # Успешно загрузили, выходим из цикла
                    else:
                        logger.warning(f"⚠️ Не удалось распарсить изображение из {img_source[:50]}")
                        continue
                else:
                    # === ЛОКАЛЬНЫЙ ФАЙЛ ===
                    if os.path.exists(img_source):
                        if pixmap.load(img_source):
                            logger.info(f"✅ Загружен локальный файл: {img_source}")
                            break
                        else:
                            logger.warning(f"⚠️ Не удалось загрузить файл: {img_source}")
                    else:
                        logger.debug(f"📁 Файл не найден: {img_source}")
                        continue
                        
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки из {img_source[:50]}: {type(e).__name__}")
                continue
        
        # Показываем результат
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.image_label.size() - QSize(20, 20),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setText("")
            self.image_label.setStyleSheet("""
                QLabel {
                    background-color: #1e1e1e;
                    border: 1px solid #444;
                    border-radius: 3px;
                    padding: 5px;
                }
            """)
        else:
            self._clear_image_preview()
            return
        
        # Обновляем информацию
        info_text = f"<b>{part['name']}</b><br>"
        if part.get('part_type'):
            info_text += f"Тип: {part['part_type']}<br>"
        if part.get('package'):
            info_text += f"Корпус: {part['package']}<br>"
        info_text += f"Количество: {part['quantity']}<br>"
        info_text += f"Цена: {part['price']:.2f} ₽"
        self.info_label.setText(info_text)
    
    def _clear_image_preview(self):
        """Очистить предпросмотр."""
        self.image_label.setText("📷\nИзображение\nне выбрано")
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px dashed #555;
                border-radius: 5px;
                color: #888;
            }
        """)
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
                if parent_item:
                    parent_item.appendRow(item)
                else:
                    root_item.appendRow(item)

    def _on_category_click(self, index):
        cat_id = self.tree_model.data(index, Qt.UserRole)
        self.parts_model.load_data(cat_id, self.current_filter)
        self._update_status()

    def _filter_table(self, text):
        self.filter_model.set_search_text(text)
    
    def _update_status(self):
        stats = self.db.get_stats()
        filter_text = {
            "all": "Все",
            "in_stock": "В наличии",
            "low_stock": "Мало",
            "out_of_stock": "Нет на складе"
        }.get(self.current_filter, "Все")
        
        self.status.showMessage(f"📦 Всего: {stats['total_parts']} позиций | 💰 Стоимость: {stats['total_value']:.2f}₽ | ⚠️ Нет в наличии: {stats['out_of_stock']} | 🔍 Фильтр: {filter_text}")
    
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
            self.parts_model.load_data(self._get_selected_category(), self.current_filter)
            self._load_categories()
            self._update_status()
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
                self.parts_model.load_data(self._get_selected_category(), self.current_filter)
                self._load_categories()
                self._update_status()
                QMessageBox.information(self, "✅ Успех", "Компонент обновлён!")
    
    def _delete_part(self):
        indexes = self.parts_table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "️ Внимание", "Выберите компонент для удаления")
            return
        row = indexes[0].row()
        part_id = int(self.filter_model.data(self.filter_model.index(row, 0)))
        part_name = self.filter_model.data(self.filter_model.index(row, 1))
        if QMessageBox.question(self, "❓ Подтверждение", f"Удалить \"{part_name}\"?\n\nДанные будут перемещены в архив.", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete_part(part_id)
            self.parts_model.load_data(self._get_selected_category(), self.current_filter)
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
                    self.parts_model.load_data(self._get_selected_category(), self.current_filter)
                    self._load_categories()
                    self._update_status()
                    QMessageBox.information(self, "Результат", f"✅ Импорт завершен!\nДобавлено: {imported}\nОшибок: {errors}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка импорта", str(e))