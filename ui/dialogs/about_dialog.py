# ui/dialogs/about_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from config import APP_NAME, APP_VERSION

class AboutDialog(QDialog):
    """Окно 'О программе': версия, лицензия, автор."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"О программе {APP_NAME}")
        self.setMinimumWidth(450)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel(f"<h2>{APP_NAME}</h2>")
        title.setAlignment(Qt.AlignCenter)

        version = QLabel(f"<b>Версия:</b> {APP_VERSION}")
        version.setAlignment(Qt.AlignCenter)

        desc = QLabel("Приложение для учёта радиокомпонентов и быстрого поиска по местам хранения.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)

        license_info = QLabel(
            "<b>Лицензия:</b> MIT License<br>"
            "<b>Автор:</b> Dykus &copy; 2026<br>"
            "<b>Исходный код:</b> <a href='https://github.com/Dykus/radio-parts-db'>GitHub</a>"
        )
        license_info.setAlignment(Qt.AlignCenter)
        license_info.setOpenExternalLinks(True)

        close_btn = QPushButton("Закрыть")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)

        layout.addSpacing(30)
        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(desc)
        layout.addWidget(license_info)
        layout.addSpacing(20)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)