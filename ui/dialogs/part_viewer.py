# ui/dialogs/part_viewer.py
import os
import urllib.request
import ssl
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QWidget, QFrame, QTextEdit, QScrollArea,
    QComboBox
)
from PySide6.QtCore import Qt, QEvent, QSize
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument
from .part_dialog import PartDialog

class NotesWindow(QDialog):
    """Отдельное окно для просмотра заметок с возможностью изменения шрифта."""
    def __init__(self, notes_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Заметки")
        self.setMinimumSize(500, 400)
        self.resize(600, 500)
        self.notes_text = notes_text
        self.current_font_size = 10
        self._init_ui()
        self._fill_notes()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Панель инструментов для изменения шрифта
        toolbar = QHBoxLayout()
        self.font_size_label = QLabel("Размер шрифта:")
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32"])
        self.font_size_combo.setCurrentText("10")
        self.font_size_combo.currentTextChanged.connect(self._change_font_size)
        self.btn_zoom_in = QPushButton("➕")
        self.btn_zoom_in.clicked.connect(lambda: self._change_font_size_delta(1))
        self.btn_zoom_out = QPushButton("➖")
        self.btn_zoom_out.clicked.connect(lambda: self._change_font_size_delta(-1))
        toolbar.addWidget(self.font_size_label)
        toolbar.addWidget(self.font_size_combo)
        toolbar.addWidget(self.btn_zoom_in)
        toolbar.addWidget(self.btn_zoom_out)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Поле заметок (только чтение)
        self.notes_edit = QTextEdit()
        self.notes_edit.setReadOnly(True)
        self.notes_edit.setStyleSheet("background-color: #ffffff; border: 1px solid #cccccc;")
        layout.addWidget(self.notes_edit)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

    def _change_font_size(self, size_str):
        try:
            size = int(size_str)
            self.current_font_size = size
            font = QFont()
            font.setPointSize(size)
            self.notes_edit.setFont(font)
        except:
            pass

    def _change_font_size_delta(self, delta):
        new_size = self.current_font_size + delta
        if 6 <= new_size <= 72:
            self.current_font_size = new_size
            self.font_size_combo.setCurrentText(str(new_size))
            font = QFont()
            font.setPointSize(new_size)
            self.notes_edit.setFont(font)

    def _fill_notes(self):
        self.notes_edit.setPlainText(self.notes_text if self.notes_text else "—")


class ImageZoomWindow(QDialog):
    """Окно для увеличенного просмотра изображения с зумом колёсиком."""
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Увеличенное изображение")
        self.setMinimumSize(400, 300)
        self.original_pixmap = pixmap
        self.current_zoom = 1.0
        self._init_ui()

    def _init_ui(self):
        from PySide6.QtWidgets import QScrollArea, QSizePolicy
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
        self.scroll_area.viewport().installEventFilter(self)

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
    """Окно просмотра детали с прокруткой содержимого (адаптивное)."""
    def __init__(self, part_data, db, parent=None):
        super().__init__(parent)
        self.part_data = part_data
        self.db = db
        self.setWindowTitle(f"Просмотр детали: {part_data.get('name', 'Без имени')}")
        self.setMinimumSize(750, 550)
        self.resize(800, 620)
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.current_pixmap = None
        self._init_ui()
        self._fill_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # === Верхняя панель: наименование и статус ===
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)

        self.name_label = QLabel()
        name_font = QFont()
        name_font.setPointSize(16)
        name_font.setBold(True)
        self.name_label.setFont(name_font)
        self.name_label.setWordWrap(True)
        title_layout.addWidget(self.name_label, 1)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-weight: bold; padding: 4px 8px; border-radius: 4px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(self.status_label)

        main_layout.addWidget(title_widget)

        # === Фото и кнопки управления ===
        photo_widget = QWidget()
        photo_layout = QVBoxLayout(photo_widget)
        photo_layout.setSpacing(5)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(200, 200)
        self.image_label.setStyleSheet("border: 1px solid #cccccc; background-color: #f8f8f8; border-radius: 8px;")
        self.image_label.setScaledContents(False)
        photo_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

        img_btn_layout = QHBoxLayout()
        self.zoom_btn = QPushButton("🔍 Увеличить")
        self.zoom_btn.clicked.connect(self._zoom_image)
        self.save_img_btn = QPushButton("💾 Сохранить фото")
        self.save_img_btn.clicked.connect(self._save_image)
        img_btn_layout.addWidget(self.zoom_btn)
        img_btn_layout.addWidget(self.save_img_btn)
        photo_layout.addLayout(img_btn_layout)

        main_layout.addWidget(photo_widget, alignment=Qt.AlignCenter)

        # === Разделитель ===
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # === Прокручиваемая область для всей информации ===
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(12)

        # === Две колонки с информацией ===
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)
        info_layout.setSpacing(20)

        # Левая колонка
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setSpacing(8)
        # Правая колонка
        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setSpacing(8)

        # Определяем поля для левой колонки
        self.left_fields = {}
        left_labels = [
            ("🆔 ID:", "id"),
            ("📂 Категория:", "category"),
            ("🔧 Тип детали:", "part_type"),
            ("⚡ Номинал:", "value"),
            ("📦 Корпус:", "package"),
            ("🏭 Производитель:", "manufacturer"),
            ("🔖 Артикул:", "mpn"),
        ]
        for label_text, key in left_labels:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold;")
            value = QLabel("—")
            value.setWordWrap(True)
            row_layout.addWidget(label)
            row_layout.addWidget(value, 1)
            left_layout.addWidget(row_widget)
            self.left_fields[key] = value

        # Поля для правой колонки
        self.right_fields = {}
        right_labels = [
            ("📦 Количество:", "quantity"),
            ("💰 Цена (₽):", "price"),
            ("📍 Место:", "location"),
            ("🏷️ Статус:", "status"),
            ("📅 Дата ревизии:", "revision_date"),
        ]
        for label_text, key in right_labels:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold;")
            value = QLabel("—")
            value.setWordWrap(True)
            row_layout.addWidget(label)
            row_layout.addWidget(value, 1)
            right_layout.addWidget(row_widget)
            self.right_fields[key] = value

        info_layout.addWidget(left_col, 1)
        info_layout.addWidget(right_col, 1)
        content_layout.addWidget(info_widget)

        # === Блок размеров конденсатора (в одну строку) ===
        self.dims_widget = QWidget()
        dims_layout = QHBoxLayout(self.dims_widget)
        dims_layout.setContentsMargins(0, 0, 0, 0)
        dims_layout.setSpacing(15)
        self.diam_label = QLabel("⌀ — мм")
        self.height_label = QLabel("высота — мм")
        self.pitch_label = QLabel("шаг — мм")
        self.lead_label = QLabel("вывод — мм")
        for lbl in (self.diam_label, self.height_label, self.pitch_label, self.lead_label):
            lbl.setStyleSheet("color: #555;")
            dims_layout.addWidget(lbl)
        dims_layout.addStretch()
        content_layout.addWidget(self.dims_widget)
        self.dims_widget.setVisible(False)

        # === Даташит и заметки ===
        doc_widget = QWidget()
        doc_layout = QVBoxLayout(doc_widget)
        doc_layout.setSpacing(5)

        # Даташит
        ds_widget = QWidget()
        ds_layout = QHBoxLayout(ds_widget)
        ds_layout.setContentsMargins(0, 0, 0, 0)
        ds_label = QLabel("📄 Даташит:")
        ds_label.setStyleSheet("font-weight: bold;")
        self.datasheet_link = QLabel()
        self.datasheet_link.setOpenExternalLinks(True)
        self.datasheet_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        ds_layout.addWidget(ds_label)
        ds_layout.addWidget(self.datasheet_link, 1)
        doc_layout.addWidget(ds_widget)

        # Заметки с прокруткой и кнопкой открыть в окне
        notes_widget = QWidget()
        notes_layout = QHBoxLayout(notes_widget)
        notes_layout.setContentsMargins(0, 0, 0, 0)
        notes_label = QLabel("📝 Заметки:")
        notes_label.setStyleSheet("font-weight: bold;")
        self.notes_edit = QTextEdit()
        self.notes_edit.setReadOnly(True)
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setStyleSheet("background-color: #fafafa; border: 1px solid #ddd; border-radius: 4px;")
        self.notes_btn = QPushButton("📄 Открыть в окне")
        self.notes_btn.clicked.connect(self._open_notes_window)
        notes_layout.addWidget(notes_label)
        notes_layout.addWidget(self.notes_edit, 1)
        notes_layout.addWidget(self.notes_btn)
        doc_layout.addWidget(notes_widget)

        content_layout.addWidget(doc_widget)
        content_layout.addStretch()

        self.scroll_area.setWidget(content_widget)
        main_layout.addWidget(self.scroll_area, 1)

        # === Кнопки действий ===
        btn_layout = QHBoxLayout()
        self.btn_edit = QPushButton("✏️ Редактировать")
        self.btn_edit.clicked.connect(self._edit_part)
        self.btn_print = QPushButton("🖨️ Печать / PDF")
        self.btn_print.clicked.connect(self._print_part)
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_print)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        main_layout.addLayout(btn_layout)

        self.setStyleSheet("""
            QLabel {
                color: #333;
            }
            QPushButton {
                padding: 5px 15px;
            }
        """)

    def _open_notes_window(self):
        """Открывает отдельное окно с заметками."""
        notes_text = self.part_data.get('notes', '')
        win = NotesWindow(notes_text, self)
        win.exec()

    def _set_field(self, field_dict, key, value, suffix=""):
        if value is not None and str(value).strip() and str(value) != "None":
            text = str(value)
            if suffix:
                text += " " + suffix
            field_dict[key].setText(text)
        else:
            field_dict[key].setText("—")

    def _fill_data(self):
        # Наименование и статус
        self.name_label.setText(self.part_data.get('name', 'Без имени'))
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
        self.status_label.setStyleSheet(f"background-color: {bg}; font-weight: bold; padding: 4px 12px; border-radius: 4px;")

        # ID
        self._set_field(self.left_fields, "id", self.part_data.get('id'))
        # Категория
        cat_id = self.part_data.get('category_id')
        if cat_id:
            cat_path = self._get_category_path(cat_id)
            self._set_field(self.left_fields, "category", cat_path)
        else:
            self.left_fields["category"].setText("—")
        # Тип детали
        self._set_field(self.left_fields, "part_type", self.part_data.get('part_type'))
        # Номинал
        val_num = self.part_data.get('value_numeric')
        val_unit = self.part_data.get('value_unit')
        if val_num is not None and val_unit:
            if isinstance(val_num, float) and val_num.is_integer():
                val_num = int(val_num)
            self.left_fields["value"].setText(f"{val_num}{val_unit}")
        elif val_num is not None:
            self.left_fields["value"].setText(str(val_num))
        else:
            self.left_fields["value"].setText("—")
        # Корпус
        self._set_field(self.left_fields, "package", self.part_data.get('package'))
        # Производитель
        self._set_field(self.left_fields, "manufacturer", self.part_data.get('manufacturer'))
        # Артикул
        self._set_field(self.left_fields, "mpn", self.part_data.get('part_number'))

        # Правая колонка
        qty = self.part_data.get('quantity', 0)
        self._set_field(self.right_fields, "quantity", qty)
        if qty == 0:
            self.right_fields["quantity"].setStyleSheet("color: #d32f2f; font-weight: bold;")
        elif qty < 10:
            self.right_fields["quantity"].setStyleSheet("color: #f57c00; font-weight: bold;")
        else:
            self.right_fields["quantity"].setStyleSheet("color: #2e7d32; font-weight: bold;")

        price = self.part_data.get('price', 0)
        self._set_field(self.right_fields, "price", f"{price:.2f}")
        self._set_field(self.right_fields, "location", self.part_data.get('location'))
        self._set_field(self.right_fields, "status", status)
        self._set_field(self.right_fields, "revision_date", self.part_data.get('revision_date'))

        # Размеры конденсатора
        cat_id = self.part_data.get('category_id')
        if cat_id:
            cat_path = self._get_category_path(cat_id)
            is_capacitor = "конденсатор" in cat_path.lower()
            self.dims_widget.setVisible(is_capacitor)
            if is_capacitor:
                diam = self.part_data.get('diameter_mm')
                height = self.part_data.get('height_mm')
                pitch = self.part_data.get('lead_pitch_mm')
                lead = self.part_data.get('lead_diameter_mm')
                self.diam_label.setText(f"⌀ {diam} мм" if diam else "⌀ — мм")
                self.height_label.setText(f"высота {height} мм" if height else "высота — мм")
                self.pitch_label.setText(f"шаг {pitch} мм" if pitch else "шаг — мм")
                self.lead_label.setText(f"вывод {lead} мм" if lead else "вывод — мм")
        else:
            self.dims_widget.setVisible(False)

        # Даташит
        ds_path = self.part_data.get('datasheet_path')
        if ds_path:
            if ds_path.startswith(('http://', 'https://')):
                self.datasheet_link.setText(f'<a href="{ds_path}">Открыть в браузере</a>')
                self.datasheet_link.setToolTip(ds_path)
            else:
                if os.path.exists(ds_path):
                    self.datasheet_link.setText(f'<a href="file:///{ds_path}">Открыть файл</a>')
                else:
                    self.datasheet_link.setText("Файл не найден")
        else:
            self.datasheet_link.setText("—")

        # Заметки
        notes = self.part_data.get('notes', '')
        self.notes_edit.setPlainText(notes if notes else "—")
        # Загрузка фото
        self._load_image()

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
            self._rescale_image()
            self.image_label.setToolTip("Двойной клик для увеличения")
            self.image_label.mouseDoubleClickEvent = lambda e: self._zoom_image()
        else:
            self.current_pixmap = None
            self.image_label.setText("Нет фото")
            self.image_label.setStyleSheet("border: 1px solid #cccccc; background-color: #f8f8f8; border-radius: 8px;")

    def _rescale_image(self):
        if self.current_pixmap and not self.current_pixmap.isNull():
            scaled = self.current_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
            self.image_label.setFixedSize(scaled.size())
        else:
            self.image_label.setText("Нет фото")
            self.image_label.setFixedSize(200, 200)

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
        <tr><th>ID</th><td>{self.part_data.get('id', '')}</td></tr>
        <tr><th>Категория</th><td>{self._get_category_path(self.part_data.get('category_id')) if self.part_data.get('category_id') else '—'}</td></tr>
        <tr><th>Тип детали</th><td>{self.part_data.get('part_type', '—')}</td></tr>
        <tr><th>Номинал</th><td>{self.left_fields.get('value', QLabel()).text()}</td></tr>
        <tr><th>Корпус</th><td>{self.part_data.get('package', '—')}</td></tr>
        <tr><th>Диаметр</th><td>{self._format_dim(self.part_data.get('diameter_mm'), 'мм')}</td></tr>
        <tr><th>Высота</th><td>{self._format_dim(self.part_data.get('height_mm'), 'мм')}</td></tr>
        <tr><th>Шаг выводов</th><td>{self._format_dim(self.part_data.get('lead_pitch_mm'), 'мм')}</td></tr>
        <tr><th>Толщина выводов</th><td>{self._format_dim(self.part_data.get('lead_diameter_mm'), 'мм')}</td></tr>
        <tr><th>Количество</th><td>{self.part_data.get('quantity', 0)}</td></tr>
        <tr><th>Цена</th><td>{self.part_data.get('price', 0):.2f} ₽</td></tr>
        <tr><th>Место</th><td>{self.part_data.get('location', '—')}</td></tr>
        <tr><th>Производитель</th><td>{self.part_data.get('manufacturer', '—')}</td></tr>
        <tr><th>Артикул</th><td>{self.part_data.get('part_number', '—')}</td></tr>
        <tr><th>Дата ревизии</th><td>{self.part_data.get('revision_date', '—')}</td></tr>
        </table>
        <p><strong>Заметки:</strong><br>{self.part_data.get('notes', '')}</p>
        </body>
        </html>
        """
        return html

    def _format_dim(self, value, unit):
        if value and value > 0:
            return f"{value} {unit}"
        return "—"