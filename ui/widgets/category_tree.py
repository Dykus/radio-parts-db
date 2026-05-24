# ui/widgets/category_tree.py
import logging
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTreeView, QAbstractItemView,
    QPushButton, QInputDialog, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, Signal, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem

logger = logging.getLogger(__name__)

class CategoryTreeWidget(QWidget):
    category_selected = Signal(object)
    categories_changed = Signal()

    def __init__(self, db, parent=None, start_depth=0):
        super().__init__(parent)
        self.db = db
        self.start_depth = start_depth
        self._init_ui()
        self._setup_context_menu()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.btn_show_all = QPushButton("📂 Все категории")
        self.btn_show_all.setCheckable(True)
        self.btn_show_all.setChecked(True)
        self.btn_show_all.clicked.connect(self._on_show_all_clicked)
        layout.addWidget(self.btn_show_all)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск категорий...")
        self.search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self.search_edit)

        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree_view.setAnimated(True)

        self.tree_view.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree_view.setDefaultDropAction(Qt.MoveAction)
        self.tree_view.setDropIndicatorShown(True)
        self.tree_view.setDragEnabled(True)
        self.tree_view.viewport().setAcceptDrops(True)

        self.source_model = QStandardItemModel()
        self.source_model.setHorizontalHeaderLabels(["Категории"])

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setRecursiveFilteringEnabled(False)

        self.tree_view.setModel(self.proxy_model)
        layout.addWidget(self.tree_view)

        self.tree_view.clicked.connect(self._on_click)
        self.source_model.rowsMoved.connect(self._on_rows_moved)

    def _setup_context_menu(self):
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        index = self.tree_view.indexAt(pos)
        menu = QMenu(self)

        if not index.isValid():
            menu.addAction("➕ Добавить категорию").triggered.connect(self._add_root_category)
            menu.addSeparator()
            menu.addAction(" Развернуть всё").triggered.connect(self.tree_view.expandAll)
            menu.addAction("🔼 Свернуть всё").triggered.connect(self.tree_view.collapseAll)
            menu.exec(self.tree_view.viewport().mapToGlobal(pos))
            return

        source_index = self.proxy_model.mapToSource(index)
        cat_id = self.source_model.data(source_index, Qt.UserRole)
        cat_name = self.source_model.data(source_index, Qt.DisplayRole)
        clean_name = re.sub(r'\s*\(\d+\)\s*$', '', cat_name)

        menu.addAction("➕ Добавить подкатегорию").triggered.connect(lambda: self._add_subcategory(cat_id))
        menu.addSeparator()
        menu.addAction(f"✏️ Переименовать «{clean_name}»").triggered.connect(lambda: self._rename_category(cat_id, clean_name))
        menu.addSeparator()
        menu.addAction("🗑️ Удалить категорию").triggered.connect(lambda: self._delete_category(cat_id, clean_name))
        menu.addSeparator()
        menu.addAction("🔽 Развернуть всё").triggered.connect(self.tree_view.expandAll)
        menu.addAction("🔼 Свернуть всё").triggered.connect(self.tree_view.collapseAll)
        menu.exec(self.tree_view.viewport().mapToGlobal(pos))

    def _add_root_category(self):
        new_name, ok = QInputDialog.getText(self, "Новая категория", "Название категории: ")
        if ok and new_name.strip():
            self.db.create_category(new_name.strip(), None)
            self.categories_changed.emit()

    def _rename_category(self, cat_id, old_name):
        clean_name = re.sub(r'\s*\(\d+\)\s*$', '', old_name)
        new_name, ok = QInputDialog.getText(self, "Переименовать", "Новое название: ", text=clean_name)
        if ok and new_name.strip():
            self.db.rename_category(cat_id, new_name.strip())
            self.categories_changed.emit()

    def _add_subcategory(self, parent_id):
        new_name, ok = QInputDialog.getText(self, "Новая подкатегория", "Название: ")
        if ok and new_name.strip():
            self.db.create_category(new_name.strip(), parent_id)
            self.categories_changed.emit()

    def _delete_category(self, cat_id, name):
        children_count = self.db.get_category_children_count(cat_id)
        parts_count = self.db.get_category_part_count_recursive(cat_id)
        msg = f"Удалить категорию «{name}»?"
        if children_count > 0:
            msg += f"\n️ Внутри есть подкатегории ({children_count}). Они будут удалены."
        if parts_count > 0:
            msg += f"\n⚠️ Внутри есть детали ({parts_count}). Они станут без категории."
        if QMessageBox.warning(self, "Подтверждение удаления", msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete_category(cat_id)
            self.categories_changed.emit()

    def _on_show_all_clicked(self):
        self.tree_view.clearSelection()
        self.btn_show_all.setChecked(True)
        self.category_selected.emit(None)

    def _apply_depth_recursive(self, max_depth, current_depth=0, parent_idx=None):
        """Рекурсивно управляет раскрытием дерева вместо ненадёжного expandToDepth()"""
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

    def load_categories(self):
        self.source_model.clear()
        self.source_model.setHorizontalHeaderLabels(["Категории"])
        root = self.source_model.invisibleRootItem()

        cats = self.db.get_categories()
        item_map = {}

        for cat_id, name, parent_id in cats:
            count = self.db.get_category_part_count_recursive(cat_id)
            text = f"{name} ({count})" if count > 0 else name
            item = QStandardItem(text)
            item.setData(cat_id, Qt.UserRole)
            item.setDragEnabled(True)
            item.setDropEnabled(True)
            item_map[cat_id] = item

        for cat_id, name, parent_id in cats:
            item = item_map[cat_id]
            if parent_id in (None, 0) or parent_id not in item_map:
                root.appendRow(item)
            else:
                item_map[parent_id].appendRow(item)

        # ✅ ПРИМЕНЯЕМ НАШУ НАДЁЖНУЮ ФУНКЦИЮ ГЛУБИНЫ
        self._apply_depth_recursive(self.start_depth)
        
        if self.source_model.rowCount() == 0:
            self._on_show_all_clicked()

    def _on_search(self, text):
        search_text = text.strip().lower()
        if not search_text:
            self.proxy_model.setFilterFixedString("")
            self._apply_depth_recursive(self.start_depth)
            return
        
        self.proxy_model.setFilterFixedString(text)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.tree_view.expandAll()
        self.btn_show_all.setChecked(False)

    def _on_click(self, proxy_index):
        source_index = self.proxy_model.mapToSource(proxy_index)
        cat_id = self.source_model.data(source_index, Qt.UserRole)
        self.btn_show_all.setChecked(False)
        self.category_selected.emit(cat_id if cat_id else None)

    def _on_rows_moved(self, source_parent, start, end, dest_parent, row):
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