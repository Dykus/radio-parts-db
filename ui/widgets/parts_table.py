# ui/widgets/parts_table.py
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QAbstractItemView
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression, Signal
from PySide6.QtGui import QColor, QStandardItemModel, QStandardItem

logger = logging.getLogger(__name__)

class PartsTableModel(QStandardItemModel):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setHorizontalHeaderLabels(["ID", "Наименование", "Тип", "Корпус", "Кол-во", "Цена", "Место", "Состояние"])
        self.load_data()

    def _format_package_with_dimensions(self, package, dims):
        """Формирует строку для колонки «Корпус»: package + размеры (если есть)"""
        if not dims:
            return package or ''
        parts = []
        if package:
            parts.append(package)
        # Безопасно получаем значения, заменяя None на 0
        diam = dims.get('diameter_mm') or 0
        height = dims.get('height_mm') or 0
        pitch = dims.get('lead_pitch_mm') or 0
        lead_d = dims.get('lead_diameter_mm') or 0
        if diam > 0 and height > 0:
            parts.append(f"⌀{diam}×{height}мм")
        elif diam > 0:
            parts.append(f"⌀{diam}мм")
        elif height > 0:
            parts.append(f"высота {height}мм")
        if pitch > 0:
            parts.append(f"шаг {pitch}мм")
        if lead_d > 0:
            parts.append(f"вывод {lead_d}мм")
        return ' / '.join(parts) if parts else (package or '')

    def load_data(self, category_id=None, filter_type="all", location_path=None):
        self.removeRows(0, self.rowCount())
        parts = self.db.get_all_parts_filtered(category_id, filter_type, location_path)
        
        status_cell_colors = {
            "Новое": ("#a5d6a7", "#000000"),
            "Отличное": ("#a5d6a7", "#000000"),
            "Б/У проверено": ("#90caf9", "#000000"),
            "Б/У не проверено": ("#fff59d", "#000000"),
            "Плохое": ("#ffcc80", "#000000"),
            "Неисправно": ("#ef9a9a", "#000000")
        }
        
        for p in parts:
            has_photo = bool(p.get('image_path') and p['image_path'].strip())
            package_text = p.get('package') or ''
            dims = {
                'diameter_mm': p.get('diameter_mm'),
                'height_mm': p.get('height_mm'),
                'lead_pitch_mm': p.get('lead_pitch_mm'),
                'lead_diameter_mm': p.get('lead_diameter_mm'),
            }
            display_package = self._format_package_with_dimensions(package_text, dims)
            if has_photo:
                display_package = f"📷 {display_package}"
            
            items = [
                QStandardItem(str(p['id'])),
                QStandardItem(p['name']),
                QStandardItem(p['part_type'] or ''),
                QStandardItem(display_package),
                QStandardItem(str(p['quantity'])),
                QStandardItem(f"{p['price']:.2f}"),
                QStandardItem(p['location'] or ''),
                QStandardItem(p['status'] or 'Новое')
            ]
            
            qty = p['quantity']
            status = p['status']
            
            if qty == 0:
                row_bg, row_fg = QColor("#ffcdd2"), QColor("#000000")
            elif qty < 10:
                row_bg, row_fg = QColor("#fff9c4"), QColor("#000000")
            else:
                row_bg, row_fg = QColor("#c8e6c9"), QColor("#000000")
            
            for item in items:
                item.setBackground(row_bg)
                item.setForeground(row_fg)
                item.setEditable(False)
            
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
        
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSortIndicatorShown(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        self.table_view.horizontalHeader().setSectionsMovable(True)
        self.table_view.horizontalHeader().setDragEnabled(True)
        self.table_view.setDragDropMode(QAbstractItemView.InternalMove)
        
        self.table_view.hideColumn(0)

        self.table_view.selectionModel().selectionChanged.connect(self._on_selection)
        self.table_view.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table_view)

    def get_column_order(self):
        header = self.table_view.horizontalHeader()
        return [header.logicalIndex(i) for i in range(header.count())]

    def set_column_order(self, order):
        if not order:
            return
        header = self.table_view.horizontalHeader()
        for target_pos, logical_idx in enumerate(order):
            current_pos = header.visualIndex(logical_idx)
            if current_pos != -1 and current_pos != target_pos:
                header.moveSection(current_pos, target_pos)

    def _on_selection(self, selected, deselected):
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            self.selection_changed.emit(0)
            return
        row = indexes[0].row()
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
        if not indexes:
            return None
        row = indexes[0].row()
        return int(self.proxy_model.data(self.proxy_model.index(row, 0)))