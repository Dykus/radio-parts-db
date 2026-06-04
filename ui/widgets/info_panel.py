# ui/widgets/info_panel.py
import os
import logging
import urllib.request
import ssl
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QStyle, QMenu, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPixmap
from config import DATA_DIR

logger = logging.getLogger(__name__)

class InfoPanelWidget(QWidget):
    location_clicked = Signal(str)
    depth_changed = Signal(int)

    def __init__(self, db, parent=None, start_depth=0):
        super().__init__(parent)
        self.db = db
        self.start_depth = start_depth
        self.setStyleSheet("""
            QWidget { background-color: #f5f5f5; color: #333; }
            QLabel { color: #333; }
            QTreeWidget { background-color: #ffffff; border: 1px solid #cccccc; color: #333; }
            QTreeWidget::item:hover { background-color: #e0e0e0; }
            QTreeWidget::item:selected { background-color: #3399ff; color: white; }
            QPushButton { background-color: #e0e0e0; border: 1px solid #cccccc; border-radius: 3px; padding: 2px 5px; }
            QPushButton:hover { background-color: #d0d0d0; }
        """)
        self._init_ui()
        self._setup_context_menu()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        photo_label = QLabel("🖼️ Предпросмотр")
        photo_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(photo_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(150)
        self.image_label.setMaximumHeight(220)
        self.image_label.setStyleSheet("QLabel { background-color: #ffffff; border: 1px solid #cccccc; border-radius: 3px; }")
        self.image_label.setText("🖼️")
        self.image_label.setScaledContents(False)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.image_label)
        scroll_area.setMaximumHeight(240)
        scroll_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        layout.addWidget(scroll_area)

        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("padding: 5px; font-size: 11px;")
        layout.addWidget(self.info_label)

        nav_header_layout = QHBoxLayout()
        nav_header_layout.setContentsMargins(0, 5, 0, 5)
        location_label = QLabel("📍 Навигатор по местам")
        location_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        nav_header_layout.addWidget(location_label)
        nav_header_layout.addStretch()
        self.btn_quick_depth = QPushButton("🔄 Глубина")
        self.btn_quick_depth.setToolTip("Переключить уровень раскрытия: 0 -> 1 -> 2 -> 3 -> Всё")
        self.btn_quick_depth.setFixedSize(65, 22)
        self.btn_quick_depth.setStyleSheet("font-size: 9px;")
        self.btn_quick_depth.clicked.connect(self._cycle_depth)
        nav_header_layout.addWidget(self.btn_quick_depth)
        layout.addLayout(nav_header_layout)

        self.location_tree = QTreeWidget()
        self.location_tree.setHeaderHidden(True)
        self.location_tree.setMinimumHeight(150)
        self.location_tree.setIndentation(15)
        self.location_tree.itemClicked.connect(self._on_tree_click)
        layout.addWidget(self.location_tree)
        layout.setStretchFactor(self.location_tree, 10)

    def _cycle_depth(self):
        levels = [0, 1, 2, 3, -1]
        current = levels.index(self.start_depth) if self.start_depth in levels else 0
        next_level = levels[(current + 1) % len(levels)]
        self.start_depth = next_level
        self.depth_changed.emit(next_level)
        self.load_tree()

    def _setup_context_menu(self):
        self.location_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.location_tree.customContextMenuRequested.connect(self._show_location_context_menu)

    def _show_location_context_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("📂 Развернуть всё").triggered.connect(self.location_tree.expandAll)
        menu.addAction("📁 Свернуть всё").triggered.connect(self.location_tree.collapseAll)
        menu.exec(self.location_tree.viewport().mapToGlobal(pos))

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

    def _apply_depth_tree_widget(self, max_depth, current_depth=0, item=None):
        if max_depth == -1:
            self.location_tree.expandAll()
            return
        if item is None:
            for i in range(self.location_tree.topLevelItemCount()):
                self._apply_depth_tree_widget(max_depth, 0, self.location_tree.topLevelItem(i))
            return
        if current_depth < max_depth:
            item.setExpanded(True)
            for i in range(item.childCount()):
                self._apply_depth_tree_widget(max_depth, current_depth + 1, item.child(i))
        else:
            item.setExpanded(False)

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
        self._apply_depth_tree_widget(self.start_depth)

    def highlight_location(self, location_path):
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
                if child.text(0).strip() == target_name:
                    current_item = child
                    current_item.setExpanded(True)
                    found = True
                    break
            if not found:
                return
        self.location_tree.setCurrentItem(current_item)
        self.location_tree.scrollToItem(current_item)

    def _load_pixmap_from_url(self, url):
        """Загружает изображение по URL и возвращает QPixmap."""
        pixmap = QPixmap()
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(url, context=ctx, timeout=5) as response:
                data = response.read()
            pixmap.loadFromData(data)
        except Exception as e:
            logger.warning(f"Не удалось загрузить изображение из URL: {url} - {e}")
        return pixmap

    def update_content(self, part):
        if not part:
            self._clear_preview()
            return
        
        image_path = part.get('image_path', '').strip()
        pixmap = QPixmap()
        
        if image_path:
            if image_path.startswith(('http://', 'https://')):
                pixmap = self._load_pixmap_from_url(image_path)
            else:
                # локальный файл (имя в data/images)
                img_path = DATA_DIR / "images" / Path(image_path).name
                if img_path.exists():
                    pixmap = QPixmap(str(img_path))
        
        if not pixmap.isNull():
            scaled = pixmap.scaled(self.image_label.size() - QSize(20, 20),
                                   Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
            self.image_label.setText("")
        else:
            self.image_label.setText("🖼️")
        
        info_text = f"<b>{part['name']}</b><br>"
        if part.get('part_type'):
            info_text += f"Тип: {part['part_type']}<br>"
        if part.get('package'):
            info_text += f"Корпус: {part['package']}<br>"
        info_text += f"Кол-во: {part['quantity']} | Цена: {part['price']:.2f} ₽"
        
        self.info_label.setText(info_text)
        self.highlight_location(part.get('location', ''))

    def _clear_preview(self):
        self.image_label.clear()
        self.image_label.setText("🖼️")
        self.info_label.setText("")
        self.location_tree.clearSelection()