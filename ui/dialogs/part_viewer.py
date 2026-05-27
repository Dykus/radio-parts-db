# ui/dialogs/part_viewer.py
import os
import urllib.request
import ssl
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFileDialog, QMessageBox, QWidget, QGridLayout,
    QSizePolicy
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QPixmap
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument
from .part_dialog import PartDialog

class ImageZoomWindow(QDialog):
    # ... (без изменений, оставляем как было)
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Увеличенное изображение")
        self.setMinimumSize(400, 300)
        self.original_pixmap = pixmap
        self.current_zoom = 1.0
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)

        btn_layout = QHBoxLayout()
        self.zoom_in_btn = QPushButton("➕ Увеличить")
        self.zoom_in_btn.clicked.connect(lambda: self._zoom(1.2))
        self.zoom_out_btn = QPushButton("➖ Уменьшить")
        self.zoom_out_btn.clicked.connect(lambda: self._zoom(0.8))
        self.reset_btn = QPushButton("🔄 Сбросить")
        self.reset_btn.clicked.connect(self._reset_zoom)
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.zoom_in_btn)
        btn_layout.addWidget(self.zoom_out_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        self._update_pixmap()
        self.setMouseTracking(True)
        self.scroll_area.viewport().installEventFilter(self)
        self.image_label.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom(1.1)
            else:
                self._zoom(0.9)
            return True
        return super().eventFilter(obj, event)

    def _zoom(self, factor):
        self.current_zoom *= factor
        if self.current_zoom < 0.1:
            self.current_zoom = 0.1
        if self.current_zoom > 10.0:
            self.current_zoom = 10.0
        self._update_pixmap()

    def _reset_zoom(self):
        self.current_zoom = 1.0
        self._update_pixmap()

    def _update_pixmap(self):
        if self.original_pixmap.isNull():
            return
        new_size = self.original_pixmap.size() * self.current_zoom
        scaled = self.original_pixmap.scaled(new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self.image_label.resize(scaled.size())
        self.scroll_area.widgetResizable = False
        self.scroll_area.widgetResizable = True

class PartViewer(QDialog):
    def __init__(self, part_data, db, parent=None):
        super().__init__(parent)
        self.part_data = part_data
        self.db = db
        self.setWindowTitle(f"Просмотр детали: {part_data.get('name', 'Без имени')}")
        self.setMinimumSize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self._init_ui()
        self._fill_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        self.name_label = QLabel()
        self.name_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        top_layout.addWidget(self.name_label)
        top_layout.addStretch()
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-weight: bold; padding: 4px 8px; border-radius: 4px;")
        top_layout.addWidget(self.status_label)
        main_layout.addLayout(top_layout)

        content_splitter = QHBoxLayout()

        # Левая панель: изображение
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(200, 200)
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        self.image_label.setScaledContents(False)
        self.image_label.setMaximumSize(400, 400)
        left_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

        img_btn_layout = QHBoxLayout()
        self.zoom_btn = QPushButton("🔍 Увеличить")
        self.zoom_btn.clicked.connect(self._zoom_image)
        self.save_img_btn = QPushButton("💾 Сохранить фото")
        self.save_img_btn.clicked.connect(self._save_image)
        img_btn_layout.addWidget(self.zoom_btn)
        img_btn_layout.addWidget(self.save_img_btn)
        left_layout.addLayout(img_btn_layout)
        left_layout.addStretch()

        # Правая панель: свойства в виде сетки
        right_widget = QWidget()
        self.properties_grid = QGridLayout(right_widget)
        self.properties_grid.setColumnStretch(1, 1)
        self.properties_grid.setColumnStretch(3, 1)
        self.property_labels = {}

        properties = [
            ("ID", "id"), ("Наименование", "name"), ("Категория", "category_path"),
            ("Тип детали", "part_type"), ("Номинал", "value_nice"), ("Корпус", "package"),
            ("Диаметр (мм)", "diameter_mm"), ("Высота (мм)", "height_mm"),
            ("Шаг выводов (мм)", "lead_pitch_mm"), ("Толщина выводов (мм)", "lead_diameter_mm"),
            ("Количество", "quantity"), ("Цена (₽)", "price"), ("Место хранения", "location"),
            ("Состояние", "status"), ("Производитель", "manufacturer"), ("Артикул (MPN)", "part_number"),
            ("Дата ревизии", "revision_date")
        ]
        left_col, right_col = [], []
        for i, (label, key) in enumerate(properties):
            (left_col if i % 2 == 0 else right_col).append((label, key))
        row = 0
        for label, key in left_col:
            lbl = QLabel(label + ":")
            lbl.setStyleSheet("font-weight: bold;")
            val = QLabel()
            val.setWordWrap(True)
            self.properties_grid.addWidget(lbl, row, 0, Qt.AlignTop)
            self.properties_grid.addWidget(val, row, 1, Qt.AlignTop)
            self.property_labels[key] = val
            row += 1
        row = 0
        for label, key in right_col:
            lbl = QLabel(label + ":")
            lbl.setStyleSheet("font-weight: bold;")
            val = QLabel()
            val.setWordWrap(True)
            self.properties_grid.addWidget(lbl, row, 2, Qt.AlignTop)
            self.properties_grid.addWidget(val, row, 3, Qt.AlignTop)
            self.property_labels[key] = val
            row += 1

        # Заметки
        notes_label = QLabel("Заметки:")
        notes_label.setStyleSheet("font-weight: bold;")
        self.properties_grid.addWidget(notes_label, self.properties_grid.rowCount(), 0, 1, 2)
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setMaximumHeight(100)
        self.properties_grid.addWidget(self.notes_text, self.properties_grid.rowCount()-1, 2, 1, 2)

        # Даташит
        ds_label = QLabel("Даташит:")
        ds_label.setStyleSheet("font-weight: bold;")
        self.datasheet_link = QLabel()
        self.datasheet_link.setOpenExternalLinks(True)
        self.datasheet_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.properties_grid.addWidget(ds_label, self.properties_grid.rowCount(), 0, Qt.AlignTop)
        self.properties_grid.addWidget(self.datasheet_link, self.properties_grid.rowCount()-1, 1, 1, 3)

        content_splitter.addWidget(left_widget, 1)
        content_splitter.addWidget(right_widget, 2)
        main_layout.addLayout(content_splitter)

        # Нижние кнопки
        btn_layout = QHBoxLayout()
        btn_edit = QPushButton("✏️ Редактировать")
        btn_edit.clicked.connect(self._edit_part)
        btn_print = QPushButton("🖨️ Печать / PDF")
        btn_print.clicked.connect(self._print_part)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_print)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        main_layout.addLayout(btn_layout)

        self.current_pixmap = None

    def _fill_data(self):
        self.name_label.setText(self.part_data.get('name', ''))
        status = self.part_data.get('status', 'Новое')
        self.status_label.setText(status)
        status_colors = {
            "Новое": "#a5d6a7", "Отличное": "#a5d6a7",
            "Б/У проверено": "#90caf9",
            "Б/У не проверено": "#fff59d",
            "Плохое": "#ffcc80",
            "Неисправно": "#ef9a9a"
        }
        bg = status_colors.get(status, "#e0e0e0")
        self.status_label.setStyleSheet(f"background-color: {bg}; font-weight: bold; padding: 4px 8px; border-radius: 4px;")

        self._set_label("id", str(self.part_data.get('id', '')))
        self._set_label("name", self.part_data.get('name', ''))
        cat_id = self.part_data.get('category_id')
        if cat_id:
            path = self._get_category_path(cat_id)
            self._set_label("category_path", path)
        else:
            self._set_label("category_path", "—")
        self._set_label("part_type", self.part_data.get('part_type') or '—')
        val_num = self.part_data.get('value_numeric')
        val_unit = self.part_data.get('value_unit')
        if val_num is not None and val_unit:
            if isinstance(val_num, float) and val_num.is_integer():
                val_num = int(val_num)
            self._set_label("value_nice", f"{val_num}{val_unit}")
        elif val_num is not None:
            self._set_label("value_nice", str(val_num))
        else:
            self._set_label("value_nice", "—")
        self._set_label("package", self.part_data.get('package') or '—')
        self._set_label("diameter_mm", self._format_dim(self.part_data.get('diameter_mm'), "мм"))
        self._set_label("height_mm", self._format_dim(self.part_data.get('height_mm'), "мм"))
        self._set_label("lead_pitch_mm", self._format_dim(self.part_data.get('lead_pitch_mm'), "мм"))
        self._set_label("lead_diameter_mm", self._format_dim(self.part_data.get('lead_diameter_mm'), "мм"))
        self._set_label("quantity", str(self.part_data.get('quantity', 0)))
        price = self.part_data.get('price', 0)
        self._set_label("price", f"{price:.2f}")
        self._set_label("location", self.part_data.get('location') or '—')
        self._set_label("status", status)
        self._set_label("manufacturer", self.part_data.get('manufacturer') or '—')
        self._set_label("part_number", self.part_data.get('part_number') or '—')
        rev = self.part_data.get('revision_date')
        self._set_label("revision_date", rev if rev else '—')
        self.notes_text.setPlainText(self.part_data.get('notes') or '')
        ds_path = self.part_data.get('datasheet_path')
        if ds_path:
            if ds_path.startswith(('http://', 'https://')):
                self.datasheet_link.setText(f'<a href="{ds_path}">{ds_path}</a>')
                self.datasheet_link.setToolTip("Открыть в браузере")
            else:
                if os.path.exists(ds_path):
                    self.datasheet_link.setText(f'<a href="file:///{ds_path}">{os.path.basename(ds_path)}</a>')
                else:
                    self.datasheet_link.setText("Файл не найден")
        else:
            self.datasheet_link.setText("—")
        self._load_image()

    def _set_label(self, key, text):
        if key in self.property_labels:
            self.property_labels[key].setText(text)

    def _format_dim(self, value, unit):
        if value and value > 0:
            return f"{value} {unit}"
        return "—"

    def _get_category_path(self, cat_id):
        cats = self.db.get_categories()
        cat_map = {c[0]: (c[1], c[2]) for c in cats}
        path = []
        cur_id = cat_id
        while cur_id and cur_id in cat_map:
            name, parent_id = cat_map[cur_id]
            path.insert(0, name)
            if parent_id in (None, 0):
                break
            cur_id = parent_id
        return " / ".join(path) if path else "—"

    def _load_image(self):
        img_path = self.part_data.get('image_path')
        pixmap = QPixmap()
        if img_path:
            try:
                if img_path.startswith(('http://', 'https://')):
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    with urllib.request.urlopen(img_path, context=ctx, timeout=10) as response:
                        data = response.read()
                    pixmap.loadFromData(data)
                elif os.path.exists(img_path):
                    pixmap.load(img_path)
            except Exception as e:
                print(f"Ошибка загрузки изображения: {e}")
        if not pixmap.isNull():
            self.current_pixmap = pixmap
            scaled = pixmap.scaled(self.image_label.maximumSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
            self.image_label.setToolTip("Кликните правой кнопкой для увеличения")
        else:
            self.current_pixmap = None
            self.image_label.setText("Нет фото")
            self.image_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")

    def _zoom_image(self):
        if self.current_pixmap:
            zoom_win = ImageZoomWindow(self.current_pixmap, self)
            zoom_win.resize(800, 600)
            zoom_win.exec()
        else:
            QMessageBox.information(self, "Нет изображения", "У данной детали нет привязанного изображения.")

    def _save_image(self):
        if self.current_pixmap:
            path, _ = QFileDialog.getSaveFileName(self, "Сохранить изображение", "", "PNG (*.png);;JPEG (*.jpg)")
            if path:
                self.current_pixmap.save(path)
                QMessageBox.information(self, "Сохранено", f"Изображение сохранено в {path}")
        else:
            QMessageBox.warning(self, "Нет изображения", "Нечего сохранять.")

    def _edit_part(self):
        editor = PartDialog(parent=self, part_data=self.part_data, db=self.db, start_depth=0)
        if editor.exec():
            new_data = editor.get_data()
            self.db.update_part(self.part_data['id'], new_data)
            updated = self.db.get_part(self.part_data['id'])
            if updated:
                self.part_data = updated
                self._fill_data()
            # Обновляем главное окно (если есть метод _refresh_all)
            parent = self.parent()
            if parent and hasattr(parent, '_refresh_all'):
                parent._refresh_all()

    def _print_part(self):
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Печать карточки детали")
        if dialog.exec() != QPrintDialog.Accepted:
            return
        html = self._generate_html_for_print()
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)

    def _generate_html_for_print(self):
        html = f"""
        <html>
        <head><style>body {{ font-family: Arial, sans-serif; margin: 20px; }}</style></head>
        <body>
        <h1>{self.part_data.get('name', '')}</h1>
        <p><strong>Статус:</strong> {self.part_data.get('status', '')}</p>
        <hr>
        <table border="0">
        <tr><td><strong>ID</strong></td><td>{self.part_data.get('id', '')}</td></tr>
        <tr><td><strong>Категория</strong></td><td>{self._get_category_path(self.part_data.get('category_id')) if self.part_data.get('category_id') else '—'}</td></tr>
        <tr><td><strong>Тип детали</strong></td><td>{self.part_data.get('part_type', '—')}</td></tr>
        <tr><td><strong>Номинал</strong></td><td>{self.property_labels.get('value_nice', QLabel()).text()}</td></tr>
        <tr><td><strong>Корпус</strong></td><td>{self.part_data.get('package', '—')}</td></tr>
        <tr><td><strong>Диаметр</strong></td><td>{self._format_dim(self.part_data.get('diameter_mm'), 'мм')}</td></tr>
        <tr><td><strong>Высота</strong></td><td>{self._format_dim(self.part_data.get('height_mm'), 'мм')}</td></tr>
        <tr><td><strong>Шаг выводов</strong></td><td>{self._format_dim(self.part_data.get('lead_pitch_mm'), 'мм')}</td></tr>
        <tr><td><strong>Толщина выводов</strong></td><td>{self._format_dim(self.part_data.get('lead_diameter_mm'), 'мм')}</td></tr>
        <tr><td><strong>Количество</strong></td><td>{self.part_data.get('quantity', 0)}</td></tr>
        <tr><td><strong>Цена</strong></td><td>{self.part_data.get('price', 0):.2f} ₽</td></tr>
        <tr><td><strong>Место</strong></td><td>{self.part_data.get('location', '—')}</td></tr>
        <tr><td><strong>Производитель</strong></td><td>{self.part_data.get('manufacturer', '—')}</td></tr>
        <tr><td><strong>Артикул</strong></td><td>{self.part_data.get('part_number', '—')}</td></tr>
        <tr><td><strong>Дата ревизии</strong></td><td>{self.part_data.get('revision_date', '—')}</td></tr>
        </table>
        <p><strong>Заметки:</strong><br>{self.part_data.get('notes', '')}</p>
        </body>
        </html>
        """
        return html