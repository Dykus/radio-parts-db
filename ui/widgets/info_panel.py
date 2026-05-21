# ui/widgets/info_panel.py
import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QTreeWidget, QTreeWidgetItem, QStyle
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap

logger = logging.getLogger(__name__)

class InfoPanelWidget(QWidget):
    """Правая панель: Предпросмотр фото и Навигатор по местам."""
    location_clicked = Signal(str)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # --- Секция фото ---
        photo_label = QLabel("🖼️ Предпросмотр")
        photo_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(photo_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(150)
        self.image_label.setMaximumHeight(220)  # 🔒 Ограничиваем высоту, чтобы не вытеснять дерево
        self.image_label.setStyleSheet(
            "QLabel { background-color: palette(mid); border: 1px solid palette(dark); border-radius: 3px; color: palette(text); }"
        )
        self.image_label.setText("📷")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.image_label)
        scroll_area.setMaximumHeight(240)  # 🔒 Фиксируем максимум области скролла
        layout.addWidget(scroll_area)

        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("padding: 5px; font-size: 11px;")
        layout.addWidget(self.info_label)

        # --- Секция навигатора ---
        location_label = QLabel("📍 Навигатор по местам")
        location_label.setStyleSheet("font-size: 12px; font-weight: bold; margin-top: 5px;")
        layout.addWidget(location_label)

        self.location_tree = QTreeWidget()
        self.location_tree.setHeaderHidden(True)
        self.location_tree.setMinimumHeight(150)  # 🔒 Гарантируем место для дерева
        self.location_tree.setStyleSheet(
            "QTreeWidget { background-color: palette(base); border: 1px solid palette(mid); color: palette(text); }"
            "QTreeWidget::item:hover { background-color: palette(highlight); color: palette(highlighted-text); }"
            "QTreeWidget::item:selected { background-color: palette(highlight); color: palette(highlighted-text); }"
        )
        self.location_tree.itemClicked.connect(self._on_tree_click)
        layout.addWidget(self.location_tree)
        
        # Растягиваем дерево, чтобы оно занимало всё оставшееся место
        layout.setStretchFactor(self.location_tree, 10)

    def _on_tree_click(self, item, column):
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

        self.location_clicked.emit(full_path)

    def load_tree(self):
        self.location_tree.clear()
        tree_data = self.db.get_location_tree()

        def build_tree(data_dict, parent_item):
            for key, value in sorted(data_dict.items()):
                item = QTreeWidgetItem(parent_item, [key])
                item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
                build_tree(value, item)

        root = QTreeWidgetItem(self.location_tree, ["🏠 Все места"])
        root.setIcon(0, self.style().standardIcon(QStyle.SP_DriveHDIcon))
        build_tree(tree_data, root)
        self.location_tree.expandAll()

    def highlight_location(self, location_path):
        if not location_path or not location_path.strip():
            self.location_tree.clearSelection()
            return

        parts = [p.strip() for p in location_path.split('/') if p.strip()]
        if not parts:
            self.location_tree.clearSelection()
            return

        root = self.location_tree.topLevelItem(0)
        if not root: return

        current_item = root
        for target_name in parts:
            found = False
            for i in range(current_item.childCount()):
                child = current_item.child(i)
                if child.text(0).strip() == target_name:
                    current_item = child
                    current_item.setExpanded(True)
                    found = True
                    break
            if not found: return

        self.location_tree.setCurrentItem(current_item)
        self.location_tree.scrollToItem(current_item)

    def update_content(self, part):
        if not part:
            self._clear_preview()
            return

        image_path = part.get('image_path', '').strip()
        pixmap = QPixmap()

        if image_path:
            try:
                if image_path.startswith(('http://', 'https://')):
                    import urllib.request, ssl
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    with urllib.request.urlopen(image_path, context=ctx, timeout=5) as response:
                        if pixmap.loadFromData(response.read()): pass
                elif os.path.exists(image_path):
                    pixmap.load(image_path)
            except Exception: pass

        if not pixmap.isNull():
            self.image_label.setPixmap(
                pixmap.scaled(self.image_label.size() - QSize(20, 20), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self.image_label.setStyleSheet(
                "QLabel { background-color: palette(base); border: 1px solid palette(mid); border-radius: 3px; padding: 5px; }"
            )
            self.image_label.setText("")
        else:
            self.image_label.setText("📷")
            self.image_label.setStyleSheet(
                "QLabel { background-color: palette(mid); border: 1px solid palette(dark); border-radius: 3px; color: palette(text); }"
            )

        info_text = f"<b>{part['name']}</b><br>"
        if part.get('part_type'): info_text += f"Тип: {part['part_type']}<br>"
        if part.get('package'): info_text += f"Корпус: {part['package']}<br>"
        info_text += f"Кол-во: {part['quantity']} | Цена: {part['price']:.2f} ₽"
        self.info_label.setText(info_text)

        self.highlight_location(part.get('location', ''))

    def _clear_preview(self):
        self.image_label.setText("📷")
        self.image_label.setStyleSheet("QLabel { background-color: palette(mid); border: 1px solid palette(dark); border-radius: 3px; color: palette(text); }")
        self.info_label.setText("")
        self.location_tree.clearSelection()