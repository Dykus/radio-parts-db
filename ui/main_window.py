# ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QTableView, QHeaderView, QPushButton, QLineEdit,
    QStatusBar, QLabel, QDialog, QFormLayout, QComboBox, 
    QSpinBox, QDoubleSpinBox, QDateTimeEdit, QTextEdit,
    QDialogButtonBox, QAbstractItemView, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression
from PySide6.QtGui import QColor, QStandardItemModel, QStandardItem, QRegularExpressionValidator

from core.database import Database


class PartDialog(QDialog):
    """Диалог добавления/редактирования компонента."""
    
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
        
        # Основные поля
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Например: Резистор 10кОм 0805")
        
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.setPlaceholderText("Выберите или введите")
        self._load_categories()
        
        self.part_type_edit = QLineEdit()
        self.package_combo = QComboBox()
        self.package_combo.setEditable(True)
        self.package_combo.addItems(["0402", "0603", "0805", "1206", "SOT-23", "SOIC-8", "DIP-8", "TQFP-48"])
        
        self.manufacturer_edit = QLineEdit()
        self.part_number_edit = QLineEdit()
        
        # Учёт
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
        
        # Медиа
        self.image_path_edit = QLineEdit()
        self.image_btn = QPushButton("🖼️ Обзор...")
        self.image_btn.clicked.connect(lambda: self._browse_file(self.image_path_edit, "Изображения (*.png *.jpg *.jpeg *.gif)"))
        
        self.datasheet_path_edit = QLineEdit()
        self.datasheet_btn = QPushButton("📄 Обзор...")
        self.datasheet_btn.clicked.connect(lambda: self._browse_file(self.datasheet_path_edit, "PDF (*.pdf)"))
        
        # Дата и заметки
        self.revision_date = QDateTimeEdit()
        self.revision_date.setDisplayFormat("dd.MM.yyyy")
        self.revision_date.setCalendarPopup(True)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("Дополнительные заметки...")
        
        # Добавляем в форму
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
        
        # Медиа в одну строку
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
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def _load_categories(self):
        """Загрузить категории из БД."""
        if self.db:
            cats = self.db.get_categories()
            self.category_combo.addItems([""] + [c[1] for c in cats])
    
    def _browse_file(self, line_edit, filter_str):
        """Открыть диалог выбора файла."""
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", filter_str)
        if path:
            line_edit.setText(path)
    
    def _fill_form(self, data):
        """Заполнить форму данными."""
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
        if data.get('revision_date'):
            self.revision_date.setDate(data['revision_date'])
    
    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "⚠️ Наименование обязательно!")
            return
        self.accept()
    
    def get_data(self):
        """Вернуть данные из формы."""
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
    """Модель таблицы с цветовой индикацией."""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setHorizontalHeaderLabels(["ID", "Наименование", "Тип", "Корпус", "Кол-во", "Цена", "Место", "Статус"])
        self.load_data()
    
    def load_data(self, category_id=None):
        self.removeRows(0, self.rowCount())
        parts = self.db.get_all_parts(category_id)
        
        for p in parts:
            items = [
                QStandardItem(str(p['id'])),
                QStandardItem(p['name']),
                QStandardItem(p['part_type'] or ''),
                QStandardItem(p['package'] or ''),
                QStandardItem(str(p['quantity'])),
                QStandardItem(f"{p['price']:.2f}"),
                QStandardItem(p['location'] or ''),
                QStandardItem(p['status'] or 'new')
            ]
            # Цветовая индикация с ЧЁРНЫМ текстом для контраста
            qty = p['quantity']
            status = p['status']
            if status == 'broken' or qty == 0:
                bg = QColor("#ffcdd2")  # красный светлый
                fg = QColor("#000000")  # чёрный текст
            elif qty < 10:
                bg = QColor("#fff9c4")  # жёлтый светлый
                fg = QColor("#000000")  # чёрный текст
            else:
                bg = QColor("#c8e6c9")  # зелёный светлый
                fg = QColor("#000000")  # чёрный текст
            
            for item in items:
                item.setBackground(bg)
                item.setForeground(fg)  # Устанавливаем цвет текста
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
        self.setWindowTitle("📦 RadioPartsDB v0.1.0")
        self.setMinimumSize(1200, 700)
        self._init_ui()
    
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Панель инструментов
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self._add_part)
        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.clicked.connect(self._edit_part)
        self.del_btn = QPushButton("🗑️ Удалить")
        self.del_btn.clicked.connect(self._delete_part)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск...")
        self.search_edit.textChanged.connect(self._filter_table)
        
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.del_btn)
        toolbar.addStretch()
        toolbar.addWidget(self.search_edit)
        main_layout.addLayout(toolbar)
        
        # Таблица
        splitter = QSplitter(Qt.Horizontal)
        
        self.parts_model = PartsTableModel(self.db)
        self.filter_model = PartsFilterProxyModel()
        self.filter_model.setSourceModel(self.parts_model)
        
        self.parts_table = QTableView()
        self.parts_table.setModel(self.filter_model)
        self.parts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.parts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.parts_table.doubleClicked.connect(self._edit_part)
        
        splitter.addWidget(self.parts_table)
        splitter.setSizes([950])
        main_layout.addWidget(splitter)
        
        # Статус-бар
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._update_status()
    
    def _filter_table(self, text):
        self.filter_model.set_search_text(text)
    
    def _update_status(self):
        stats = self.db.get_stats()
        self.status.showMessage(f"📦 Всего: {stats['total_parts']} позиций | 💰 Стоимость: {stats['total_value']:.2f}₽ | ⚠️ Нет в наличии: {stats['out_of_stock']}")
    
    def _add_part(self):
        dialog = PartDialog(self, db=self.db)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            # Простая логика: если категории нет в БД — добавляем
            cat_name = data['category']
            if cat_name:
                cats = self.db.get_categories()
                cat_id = None
                for c in cats:
                    if c[1] == cat_name:
                        cat_id = c[0]
                        break
                if cat_id is None:
                    cat_id = self.db.create_category(cat_name)
                data['category_id'] = cat_id
            
            self.db.create_part(data)
            self.parts_model.load_data()
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
                data = dialog.get_data()
                self.db.update_part(part_id, data)
                self.parts_model.load_data()
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
        
        reply = QMessageBox.question(
            self, "❓ Подтверждение", 
            f"Удалить компонент \"{part_name}\"?\n\nДанные будут перемещены в архив.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.delete_part(part_id)
            self.parts_model.load_data()
            self._update_status()
            QMessageBox.information(self, "✅ Успех", "Компонент удалён и архивирован")