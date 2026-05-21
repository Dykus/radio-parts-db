# ui/widgets/category_tree.py
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTreeView, QAbstractItemView, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QSortFilterProxyModel, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem

logger = logging.getLogger(__name__)

class CategoryTreeWidget(QWidget):
    """
    Левая панель: Дерево категорий с поиском, Drag-and-Drop и счётчиками.
    Сигналы:
        category_selected(cat_id): Испускается при клике на категорию (None = "Все")
        categories_changed(): Испускается при перемещении категорий
    """
    category_selected = Signal(object)  # int or None
    categories_changed = Signal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 📂 Кнопка сброса "Все категории"
        self.btn_show_all = QPushButton("📂 Все категории")
        self.btn_show_all.setCheckable(True)
        self.btn_show_all.setChecked(True) # По умолчанию активна
        self.btn_show_all.clicked.connect(self._on_show_all_clicked)
        layout.addWidget(self.btn_show_all)

        # 🔍 Поиск
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск категорий...")
        self.search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self.search_edit)

        # 🌳 Дерево
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree_view.setAnimated(True)

        # 🖱 Drag-and-Drop
        self.tree_view.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree_view.setDefaultDropAction(Qt.MoveAction)
        self.tree_view.setDropIndicatorShown(True)
        self.tree_view.setDragEnabled(True)
        self.tree_view.viewport().setAcceptDrops(True)

        # Модели
        self.source_model = QStandardItemModel()
        self.source_model.setHorizontalHeaderLabels(["Категории"])

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setRecursiveFilteringEnabled(True)

        self.tree_view.setModel(self.proxy_model)
        layout.addWidget(self.tree_view)

        # Сигналы
        self.tree_view.clicked.connect(self._on_click)
        self.source_model.rowsMoved.connect(self._on_rows_moved)

    def _on_show_all_clicked(self):
        """При клике на 'Все категории' сбрасываем выделение и фильтр."""
        self.tree_view.clearSelection()
        self.btn_show_all.setChecked(True)
        self.category_selected.emit(None)

    def load_categories(self):
        """Загружает категории из БД, считает детали рекурсивно и строит дерево."""
        # Если дерево пустое, считаем это первым запуском
        is_empty = self.source_model.rowCount() == 0
        
        self.source_model.clear()
        self.source_model.setHorizontalHeaderLabels(["Категории"])
        root = self.source_model.invisibleRootItem()

        cats = self.db.get_categories()
        item_map = {}

        # 1. Создаём элементы с рекурсивными счётчиками
        for cat_id, name, parent_id in cats:
            count = self.db.get_category_part_count_recursive(cat_id)
            text = f"{name} ({count})" if count > 0 else name
            item = QStandardItem(text)
            item.setData(cat_id, Qt.UserRole)
            item.setDragEnabled(True)
            item.setDropEnabled(True)
            item_map[cat_id] = item

        # 2. Связываем иерархию
        for cat_id, name, parent_id in cats:
            item = item_map[cat_id]
            if parent_id in (None, 0) or parent_id not in item_map:
                root.appendRow(item)
            else:
                item_map[parent_id].appendRow(item)

        self.tree_view.expandAll()
        
        # Если дерево было пустым (старт программы), выбираем "Все"
        if is_empty:
            self._on_show_all_clicked()

    def _on_search(self, text):
        self.proxy_model.setFilterFixedString(text)
        if text:
            self.tree_view.expandAll()
            self.btn_show_all.setChecked(False) # Снимаем галочку "Все", так как идет поиск
        else:
            self.tree_view.collapseAll()
            self.tree_view.expandToDepth(1)

    def _on_click(self, proxy_index):
        source_index = self.proxy_model.mapToSource(proxy_index)
        cat_id = self.source_model.data(source_index, Qt.UserRole)
        
        # Снимаем галочку с "Все категории", так как выбрана конкретная
        self.btn_show_all.setChecked(False)
        
        self.category_selected.emit(cat_id if cat_id else None)

    def _on_rows_moved(self, source_parent, start, end, dest_parent, row):
        """Обрабатывает перемещение категорий и обновляет БД."""
        src_idx = self.source_model.index(start, 0, source_parent)
        moved_item = self.source_model.itemFromIndex(src_idx)
        cat_id = moved_item.data(Qt.UserRole)

        if dest_parent.isValid():
            parent_item = self.source_model.itemFromIndex(dest_parent)
            new_parent_id = parent_item.data(Qt.UserRole) if parent_item else None
        else:
            new_parent_id = None

        old_parent_item = moved_item.parent()
        old_parent_id = old_parent_item.data(Qt.UserRole) if old_parent_item else None

        if new_parent_id != old_parent_id:
            logger.info(f"🔄 Перемещение категории #{cat_id}: parent {old_parent_id} -> {new_parent_id}")
            self.db.move_category(cat_id, new_parent_id)
            self.categories_changed.emit()
            self.load_categories()