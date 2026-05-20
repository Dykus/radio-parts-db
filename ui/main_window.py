from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("RadioPartsDB v0.1.0")
        self.setMinimumSize(1024, 600)
        self._init_ui()

    def _init_ui(self):
        cw = QWidget()
        layout = QVBoxLayout(cw)
        lbl = QLabel("🎯 RadioPartsDB запущен!\n\nЗдесь будет таблица компонентов и дерево каталога.")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size:14px; padding:20px;")
        layout.addWidget(lbl)
        self.setCentralWidget(cw)