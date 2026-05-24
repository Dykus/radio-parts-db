# ui/dialogs/category_selector.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeView, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem

class CategorySelectorDialog(QDialog):
    """Диалог выбора категории с древовидным представлением."""
    category_selected = Signal(str)

    def __init__(self, parent=None, db=None, selected_category="", start_depth=0):
        super().__init__(parent)
        self.db = db
        self.selected_category = selected_category
        self.start_depth = start_depth  # Глубина раскрытия
        self.setWindowTitle(" Выбор категории")
        self.setMinimumSize(400, 500)
        self._init_ui()
        self._load_categories()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Дерево категорий
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(20)
        
        # Включаем сортировку по алфавиту
        self.tree_view.setSortingEnabled(True)
        self.tree_view.sortByColumn(0, Qt.AscendingOrder)
        
        layout.addWidget(self.tree_view)

        # Кнопки
        button_layout = QHBoxLayout()
        
        self.btn_select = QPushButton("✅ Выбрать")
        self.btn_select.clicked.connect(self._on_select)
        button_layout.addWidget(self.btn_select)
        
        self.btn_cancel = QPushButton("❌ Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)

        # Сигнал двойного клика
        self.tree_view.doubleClicked.connect(self._on_select)

    def _get_category_path(self, index):
        """Строит полный путь категории через /"""
        path_parts = []
        current_index = index
        
        while current_index.isValid():
            item = self.tree_view.model().itemFromIndex(current_index)
            if item:
                path_parts.insert(0, item.text())
                parent_item = item.parent()
                if parent_item:
                    current_index = parent_item.index()
                else:
                    break
            else:
                break
        
        return " / ".join(path_parts)

    def _apply_depth_recursive(self, max_depth, current_depth=0, parent_idx=None):
        """Рекурсивно управляет раскрытием дерева"""
        if max_depth == -1:
            self.tree_view.expandAll()
            return
        
        model = self.tree_view.model()
        if parent_idx is None:
            for row in range(model.rowCount()):
                idx = model.index(row, 0)
                self._apply_depth_recursive(max_depth, 0, idx)
            return

        if current_depth < max_depth:
            self.tree_view.setExpanded(parent_idx, True)
            for row in range(model.rowCount(parent_idx)):
                child_idx = model.index(row, 0, parent_idx)
                self._apply_depth_recursive(max_depth, current_depth + 1, child_idx)
        else:
            self.tree_view.setExpanded(parent_idx, False)

    def _load_categories(self):
        """Загружает категории из БД и строит дерево."""
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Категории"])
        root = model.invisibleRootItem()

        cats = self.db.get_categories()
        item_map = {}

        # Создаём элементы
        for cat_id, name, parent_id in cats:
            item = QStandardItem(name)
            item.setData(cat_id, Qt.UserRole)
            item_map[cat_id] = item

        # Связываем иерархию
        for cat_id, name, parent_id in cats:
            item = item_map[cat_id]
            if parent_id in (None, 0) or parent_id not in item_map:
                root.appendRow(item)
            else:
                item_map[parent_id].appendRow(item)

        self.tree_view.setModel(model)
        
        # ✅ ПРИМЕНЯЕМ НАДЁЖНУЮ ФУНКЦИЮ ГЛУБИНЫ
        self._apply_depth_recursive(self.start_depth)

        # Выделяем текущую категорию если есть
        if self.selected_category:
            matches = model.findItems(self.selected_category, Qt.MatchExactly | Qt.MatchRecursive)
            if matches:
                self.tree_view.setCurrentIndex(matches[0].index())
                self.tree_view.scrollTo(matches[0].index())

    def _on_select(self):
        """Обрабатывает выбор категории."""
        index = self.tree_view.currentIndex()
        if index.isValid():
            full_path = self._get_category_path(index)
            self.category_selected.emit(full_path)
            self.accept()
        else:
            self.accept()