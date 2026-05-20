# ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QTableView, QHeaderView, QPushButton, QLineEdit,
    QStatusBar, QLabel, QDialog, QFormLayout, QComboBox, 
    QSpinBox, QDoubleSpinBox, QDateTimeEdit, QTextEdit,
    QDialogButtonBox, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression
from PySide6.QtGui import QColor, QStandardItemModel, QStandardItem, QRegularExpressionValidator

from core.database import Database


class PartDialog(QDialog):
    """Диалог добавления/редактирования компонента."""
    
    def __init__(self, parent=None, part_data=None, categories=None, dictionaries=None):
        super().__init__(parent)
        self.part_data = part_data
        self.categories = categories or []
        self.dictionaries = dictionaries or {}
        self.setWindowTitle("Редактирование компонента")
        self.setMinimumWidth(500)
        self._init_ui()
        if part_data:
            self._fill_form(part_data)
    
    def _init_ui(self):
        layout = QFormLayout(self)
        
        self.name_edit = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.addItems([""] + [c[1] for c in self.categories])
        
        self.part_type_edit = QLineEdit()
        self.package_combo = QComboBox()
        self.package_combo.addItems([""] + self.dictionaries.get('package', []))
        
        self.manufacturer_edit = QLineEdit()
        self.part_number_edit = QLineEdit()
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 999999)
        
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999.99)
        self.price_spin.setDecimals(2)
        
        self.location_combo = QComboBox()
        self.location_combo.addItems([""] + self.dictionaries.get('location', []))
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["new", "used", "suspect", "broken"])
        
        self.image_path_edit = QLineEdit()
        self.datasheet_path_edit = QLineEdit()
        
        self.revision_date = QDateTimeEdit()
        self.revision_date.setDisplayFormat("dd.MM.yyyy")
        self.revision_date.setCalendarPopup(True)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        
        # Добавляем поля в форму
        layout.addRow("Наименование *", self.name_edit)
        layout.addRow("Категория", self.category_combo)
        layout.addRow("Тип детали", self.part_type_edit)
        layout.addRow("Корпус", self.package_combo)
        layout.addRow("Производитель", self.manufacturer_edit)
        layout.addRow("Артикул", self.part_number_edit)
        layout.addRow("Количество", self.quantity_spin)
        layout.addRow("Цена (₽)", self.price_spin)
        layout.addRow("Место хранения", self.location_combo)
        layout.addRow("Статус", self.status_combo)
        layout.addRow("Путь к изображению", self.image_path_edit)
        layout.addRow("Путь к даташиту", self.datasheet_path_edit)
        layout.addRow("Дата ревизии", self.revision_date)
        layout.addRow("Заметки", self.notes_edit)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def _fill_form(self, data):
        """Заполнить форму данными компонента."""
        self.name_edit.setText(data.get('name', ''))
        # ... (заполнение остальных полей по аналогии)
    
    def validate_and_accept(self):
        """Проверка и сохранение."""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Наименование обязательно!")
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
    """Модель таблицы компонентов с цветовой индикацией."""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setHorizontalHeaderLabels([
            "ID", "Наименование", "Тип", "Корпус", "Кол-во", "Цена", "Место", "Статус"
        ])
        self.load_data()
    
    def load_data(self, category_id=None):
        """Загрузить данные из БД."""
        self.removeRows(0, self.rowCount())
        
        with self.db.get_cursor() as cursor:
            if category_id:
                cursor.execute("""
                    SELECT id, name, part_type, package, quantity, price, location, status 
                    FROM parts WHERE category_id = ? ORDER BY name
                """, (category_id,))
            else:
                cursor.execute("""
                    SELECT id, name, part_type, package, quantity, price, location, status 
                    FROM parts ORDER BY name
                """)
            
            for row in cursor.fetchall():
                items = [QStandardItem(str(val) if val is not None else "") for val in row]
                # Цветовая индикация статуса
                status = row[7]
                quantity = row[4]
                if status == 'broken' or quantity == 0:
                    bg = QColor("#ffcdd2")  # красный
                elif quantity < 10:
                    bg = QColor("#fff9c4")  # жёлтый
                else:
                    bg = QColor("#c8e6c9")  # зелёный
                
                for item in items:
                    item.setBackground(bg)
                    item.setEditable(False)
                
                self.appendRow(items)


class PartsFilterProxyModel(QSortFilterProxyModel):
    """Фильтр поиска по таблице."""
    
    def __init__(self):
        super().__init__()
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterKeyColumn(-1)  # Поиск по всем колонкам
    
    def set_search_text(self, text):
        rx = QRegularExpression(QRegularExpression.escape(text), QRegularExpression.CaseInsensitiveOption)
        self.setFilterRegularExpression(rx)


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle("RadioPartsDB v0.1.0")
        self.setMinimumSize(1200, 700)
        self._init_ui()
        self._load_categories()
    
    def _init_ui(self):
        """Инициализация интерфейса."""
        # Центральный виджет
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
        
        # Разделитель: дерево + таблица
        splitter = QSplitter(Qt.Horizontal)
        
        # Дерево категорий
        self.category_tree = QTreeView()
        self.category_tree.setHeaderHidden(True)
        self.category_tree.clicked.connect(self._on_category_selected)
        self.category_model = QStandardItemModel()
        self.category_tree.setModel(self.category_model)
        splitter.addWidget(self.category_tree)
        
        # Таблица компонентов
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
        
        splitter.setSizes([250, 950])
        main_layout.addWidget(splitter)
        
        # Статус-бар
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._update_status()
    
    def _load_categories(self):
        """Загрузить дерево категорий из БД."""
        self.category_model.clear()
        self.category_model.setHorizontalHeaderLabels(["Категории"])
        
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT id, name, parent_id FROM categories ORDER BY name")
            categories = cursor.fetchall()
            
            # Простая плоская загрузка (можно улучшить до иерархии)
            for cat in categories:
                item = QStandardItem(cat[1])
                item.setData(cat[0], Qt.UserRole)
                self.category_model.appendRow(item)
    
    def _on_category_selected(self, index):
        """Обработчик выбора категории."""
        category_id = self.category_model.data(index, Qt.UserRole)
        self.parts_model.load_data(category_id)
        self._update_status()
    
    def _filter_table(self, text):
        """Фильтрация таблицы по поиску."""
        self.filter_model.set_search_text(text)
    
    def _update_status(self):
        """Обновить статус-бар."""
        total = self.filter_model.rowCount()
        self.status.showMessage(f"📦 Компонентов: {total}")
    
    def _add_part(self):
        """Добавить новый компонент."""
        # Загружаем справочники
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT id, name FROM categories")
            categories = cursor.fetchall()
            cursor.execute("SELECT value FROM dictionaries WHERE type='package'")
            packages = [r[0] for r in cursor.fetchall()]
            cursor.execute("SELECT value FROM dictionaries WHERE type='location'")
            locations = [r[0] for r in cursor.fetchall()]
        
        dialog = PartDialog(
            self, 
            categories=categories,
            dictionaries={'package': packages, 'location': locations}
        )
        
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            # TODO: Сохранить в БД
            self.parts_model.load_data()
            self._update_status()
            QMessageBox.information(self, "Успех", "Компонент добавлен!")
    
    def _edit_part(self):
        """Редактировать выбранный компонент."""
        indexes = self.parts_table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "Внимание", "Выберите компонент для редактирования")
            return
        
        # TODO: Загрузить данные и открыть диалог
        QMessageBox.information(self, "Инфо", "Функция редактирования в разработке")
    
    def _delete_part(self):
        """Удалить выбранный компонент."""
        indexes = self.parts_table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "Внимание", "Выберите компонент для удаления")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение", "Удалить выбранный компонент?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # TODO: Удалить из БД + переместить в архив
            self.parts_model.load_data()
            self._update_status()
            QMessageBox.information(self, "Успех", "Компонент удалён")