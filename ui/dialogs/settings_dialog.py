# ui/dialogs/settings_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, 
    QDialogButtonBox, QLabel, QGroupBox
)
from PySide6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Настройки программы")
        self.setMinimumWidth(450)
        
        self.settings = settings if settings else {}
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # === ГРУППА: Интерфейс ===
        interface_group = QGroupBox("Интерфейс")
        form_layout = QFormLayout(interface_group)
        
        # Выпадающий список для дерева категорий
        self.category_depth_combo = QComboBox()
        self.category_depth_combo.addItem("📁 Полностью свёрнуто", 0)
        self.category_depth_combo.addItem("📂 Корни + 1 уровень", 1)
        self.category_depth_combo.addItem("📂📂 Корни + 2 уровня", 2)
        self.category_depth_combo.addItem("📂📂 Корни + 3 уровня", 3)
        self.category_depth_combo.addItem("🗂 Развернуть всё", -1)
        
        # Устанавливаем текущее значение для категорий
        current_cat_depth = self.settings.get('category_tree_depth', 0)
        for i in range(self.category_depth_combo.count()):
            if self.category_depth_combo.itemData(i) == current_cat_depth:
                self.category_depth_combo.setCurrentIndex(i)
                break
        
        # Выпадающий список для навигатора мест
        self.location_depth_combo = QComboBox()
        self.location_depth_combo.addItem("📁 Полностью свёрнуто", 0)
        self.location_depth_combo.addItem("📂 Корни + 1 уровень", 1)
        self.location_depth_combo.addItem("📂📂 Корни + 2 уровня", 2)
        self.location_depth_combo.addItem("📂📂 Корни + 3 уровня", 3)
        self.location_depth_combo.addItem("🗂 Развернуть всё", -1)
        
        # Устанавливаем текущее значение для мест
        current_loc_depth = self.settings.get('location_tree_depth', 0)
        for i in range(self.location_depth_combo.count()):
            if self.location_depth_combo.itemData(i) == current_loc_depth:
                self.location_depth_combo.setCurrentIndex(i)
                break
        
        # Выпадающий список для диалога выбора категории
        self.selector_depth_combo = QComboBox()
        self.selector_depth_combo.addItem("📁 Полностью свёрнуто", 0)
        self.selector_depth_combo.addItem("📂 Корни + 1 уровень", 1)
        self.selector_depth_combo.addItem("📂📂 Корни + 2 уровня", 2)
        self.selector_depth_combo.addItem("📂📂📂 Корни + 3 уровня", 3)
        self.selector_depth_combo.addItem("🗂 Развернуть всё", -1)
        
        # Устанавливаем текущее значение для селектора
        current_sel_depth = self.settings.get('selector_tree_depth', 0)
        for i in range(self.selector_depth_combo.count()):
            if self.selector_depth_combo.itemData(i) == current_sel_depth:
                self.selector_depth_combo.setCurrentIndex(i)
                break
        
        form_layout.addRow("Дерево категорий:", self.category_depth_combo)
        form_layout.addRow("Навигатор по местам:", self.location_depth_combo)
        form_layout.addRow("Выбор категории (диалог):", self.selector_depth_combo)
        form_layout.addRow("", QLabel("<small style='color:gray'>Настройки применяются при запуске и открытии диалогов</small>"))
        
        layout.addWidget(interface_group)
        
        # Кнопки ОК / Отмена
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self):
        """Возвращает обновленный словарь настроек."""
        return {
            'category_tree_depth': self.category_depth_combo.currentData(),
            'location_tree_depth': self.location_depth_combo.currentData(),
            'selector_tree_depth': self.selector_depth_combo.currentData()
        }