# ui/widgets/parts_table.py
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression, Signal
from PySide6.QtGui import QColor, QStandardItemModel, QStandardItem, QRegularExpressionValidator

logger = logging.getLogger(__name__)

class PartsTableModel(QStandardItemModel):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setHorizontalHeaderLabels(["ID", "Наименование", "Тип", "Корпус", "Кол-во", "Цена", "Место", "Состояние"])
        self.load_data()
    
    def load_data(self, category_id=None, filter_type="all", location_path=None):
        self.removeRows(0, self.rowCount())
        parts = self.db.get_all_parts_filtered(category_id, filter_type, location_path)
        
        # 🎨 Цвета конкретно для ячейки "Состояние"
        status_cell_colors = {
            "Новое": ("#a5d6a7", "#000000"),          # Светло-зелёный
            "Отличное": ("#a5d6a7", "#000000"),       # Светло-зелёный
            "Б/У проверено": ("#90caf9", "#000000"),  # Голубой
            "Б/У не проверено": ("#fff59d", "#000000"),# Жёлтый
            "Плохое": ("#ffcc80", "#000000"),         # Оранжевый
            "Неисправно": ("#ef9a9a", "#000000")      # Красный
        }
        
        for p in parts:
            items = [
                QStandardItem(str(p['id'])), QStandardItem(p['name']),
                QStandardItem(p['part_type'] or ''), QStandardItem(p['package'] or ''),
                QStandardItem(str(p['quantity'])), QStandardItem(f"{p['price']:.2f}"),
                QStandardItem(p['location'] or ''), QStandardItem(p['status'] or 'Новое')
            ]
            
            qty = p['quantity']
            status = p['status']
            
            # 1️⃣ Цвет фона ВСЕЙ СТРОКИ зависит от количества
            if qty == 0:
                row_bg, row_fg = QColor("#ffcdd2"), QColor("#000000")  # 🔴 Красный (нет)
            elif qty < 10:
                row_bg, row_fg = QColor("#fff9c4"), QColor("#000000")  # 🟡 Жёлтый (мало)
            else:
                row_bg, row_fg = QColor("#c8e6c9"), QColor("#000000")  # 🟢 Зелёный (много)
            
            # Применяем цвет строки ко всем ячейкам
            for item in items:
                item.setBackground(row_bg)
                item.setForeground(row_fg)
                item.setEditable(False)
            
            # 2️⃣ Переопределяем цвет ТОЛЬКО для ячейки "Состояние" (индекс 7)
            status_bg, status_fg = status_cell_colors.get(status, ("#e0e0e0", "#000000"))
            status_item = items[7]
            status_item.setBackground(QColor(status_bg))
            status_item.setForeground(QColor(status_fg))
            
            self.appendRow(items)


class PartsFilterProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterKeyColumn(-1)
    def set_search_text(self, text):
        rx = QRegularExpression(QRegularExpression.escape(text), QRegularExpression.CaseInsensitiveOption)
        self.setFilterRegularExpression(rx)


class PartsTableWidget(QWidget):
    """
    Виджет центральной таблицы компонентов.
    Отвечает за отображение, фильтрацию, сортировку и цветовую индикацию.
    """
    selection_changed = Signal(int)
    double_clicked = Signal(int)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.model = PartsTableModel(self.db)
        self.proxy_model = PartsFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # ✅ Сортировка по клику на заголовки
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSortIndicatorShown(True)
        
        # ✅ Ручное изменение ширины колонок
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # ✅ СКРЫВАЕМ КОЛОНКУ ID (индекс 0)
        self.table_view.hideColumn(0)

        # Связываем сигналы
        self.table_view.selectionModel().selectionChanged.connect(self._on_selection)
        self.table_view.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table_view)

    def _on_selection(self, selected, deselected):
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            self.selection_changed.emit(0)
            return
        
        row = indexes[0].row()
        # Получаем ID из скрытой колонки 0
        part_id = int(self.proxy_model.data(self.proxy_model.index(row, 0)))
        self.selection_changed.emit(part_id)

    def _on_double_click(self, index):
        row = index.row()
        part_id = int(self.proxy_model.data(self.proxy_model.index(row, 0)))
        self.double_clicked.emit(part_id)

    def load_data(self, category_id=None, filter_type="all", location_path=None):
        self.model.load_data(category_id, filter_type, location_path)

    def get_selected_part_id(self):
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes: return None
        row = indexes[0].row()
        return int(self.proxy_model.data(self.proxy_model.index(row, 0)))