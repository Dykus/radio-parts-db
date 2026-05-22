# ui/dialogs/help_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout, 
    QTabWidget, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class HelpDialog(QDialog):
    """
    Окно справки. Объясняет концепцию программы для "несведущих" пользователей.
    Акцент на: Зачем это нужно, Как организовать склад, Как читать цвета.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📖 Руководство пользователя")
        self.setMinimumSize(850, 650)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Вкладки справки
        tabs = QTabWidget()
        
        # === Вкладка 1: Концепция ===
        concept_tab = QWidget()
        concept_layout = QVBoxLayout(concept_tab)
        
        concept_text = QTextBrowser()
        concept_text.setOpenExternalLinks(True)
        concept_text.setFont(QFont("Segoe UI", 11))
        concept_text.setHtml(self._get_concept_text())
        concept_layout.addWidget(concept_text)
        
        tabs.addTab(concept_tab, "💡 Концепция системы")
        
        # === Вкладка 2: Пошаговый алгоритм ===
        workflow_tab = QWidget()
        workflow_layout = QVBoxLayout(workflow_tab)
        
        workflow_text = QTextBrowser()
        workflow_text.setOpenExternalLinks(True)
        workflow_text.setFont(QFont("Segoe UI", 11))
        workflow_text.setHtml(self._get_workflow_text())
        workflow_layout.addWidget(workflow_text)
        
        tabs.addTab(workflow_tab, "🚀 С чего начать")
        
        # === Вкладка 3: Правила склада ===
        rules_tab = QWidget()
        rules_layout = QVBoxLayout(rules_tab)
        
        rules_text = QTextBrowser()
        rules_text.setOpenExternalLinks(True)
        rules_text.setFont(QFont("Segoe UI", 11))
        rules_text.setHtml(self._get_rules_text())
        rules_layout.addWidget(rules_text)
        
        tabs.addTab(rules_tab, "📦 Правила хранения")
        
        # === Вкладка 4: Визуальные сигналы ===
        signals_tab = QWidget()
        signals_layout = QVBoxLayout(signals_tab)
        
        signals_text = QTextBrowser()
        signals_text.setOpenExternalLinks(True)
        signals_text.setFont(QFont("Segoe UI", 11))
        signals_text.setHtml(self._get_signals_text())
        signals_layout.addWidget(signals_text)
        
        tabs.addTab(signals_tab, "🎨 Язык цветов")
        
        layout.addWidget(tabs)
        
        # Кнопка закрытия
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Понятно, закрыть")
        close_btn.setMinimumHeight(35)
        close_btn.setMinimumWidth(150)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    # --- Тексты вкладок ---

    def _get_concept_text(self):
        return """
        <h2>💡 Концепция: "Цифровой склад"</h2>
        <p><b>RadioPartsDB</b> — это не просто табличка с цифрами. Это система, которая отвечает на два главных вопроса:</p>
        <ol>
            <li><b>Сколько у нас есть?</b> (Остатки)</li>
            <li><b>Где именно это лежит?</b> (Адресация)</li>
        </ol>
        
        <h3>Зачем это нужно?</h3>
        <p>До внедрения этой программы вы, скорее всего, тратили время на:</p>
        <ul>
            <li>🔍 Долгие поиски "того самого" конденсатора в ящике.</li>
            <li>🛒 Покупку дубликатов, потому что забыли, что деталь уже есть.</li>
            <li>📝 Бумажные журналы, которые неудобно обновлять.</li>
        </ul>
        
        <h3>Принцип работы</h3>
        <p>Мы переводим хаос в структуру. Каждая деталь получает <b>Имя</b>, <b>Тип</b> и <b>Адрес</b>. Когда вам нужна деталь, вы не бежите к шкафу с лупой — вы сначала смотрите в экран.</p>
        <p style="background-color: #c8e6c9; padding: 10px; border-radius: 5px; color: #000000;">
        <b>✨ Итог:</b> Вы покупаете только то, чего нет. Вы находите детали за 10 секунд. Вы контролируете бюджет.
        </p>
        """

    def _get_workflow_text(self):
        return """
        <h2>🚀 С чего начать? (Алгоритм)</h2>
        <p>Чтобы система заработала, нужно совершить всего 3 шага.</p>
        
        <h3>Шаг 1: Загрузка (Импорт)</h3>
        <p>Если у вас есть база в Excel или Memento Database:</p>
        <ol>
            <li>Нажмите кнопку <b>📥 Импорт CSV</b>.</li>
            <li>Выберите файл. Программа сама поймёт кодировку и разделители.</li>
            <li>Дождитесь отчета об успехе.</li>
        </ol>
        <p><i>Если базы нет — добавляйте детали вручную кнопкой ➕.</i></p>
        
        <h3>Шаг 2: Организация (Сортировка)</h3>
        <p>После импорта детали могут быть "сырыми". Приведите их в порядок:</p>
        <ul>
            <li>Проверьте <b>Категории</b> слева. Перетащите детали мышкой, если нужно (Drag-and-Drop).</li>
            <li>Проверьте <b>Места хранения</b> справа. Убедитесь, что адреса выглядят аккуратно.</li>
        </ul>
        
        <h3>Шаг 3: Эксплуатация</h3>
        <p>Теперь пользуйтесь:</p>
        <ul>
            <li>🔍 Введите "10кОм" в поиск — увидите все резисторы.</li>
            <li>📍 Кликните на "Шкаф А" — увидите всё, что там лежит.</li>
            <li>📉 Нажимайте кнопку <b>❌ Нет</b> раз в неделю, чтобы составить список закупок.</li>
        </ul>
        """

    def _get_rules_text(self):
        return """
        <h2>📦 Правила хранения (Адресация)</h2>
        <p>Главное правило хорошего склада — <b>строгая иерархия</b>.</p>
        
        <h3>🏗 Формула адреса</h3>
        <p>Мы используем 4 уровня детализации. Заполняйте их последовательно:</p>
        <pre style="background-color: #e3f2fd; padding: 15px; border-left: 5px solid #2196F3; color: #000000; font-family: 'Segoe UI', sans-serif;">
🏠 <b>Место</b> (Где? Например: "Гараж", "Офис")
   └── 📦 <b>Контейнер</b> (В чём? Например: "Шкаф 1", "Ящик с SMD")
       └── 📦 <b>Полка</b> (Где внутри? Например: "Полка 2")
           └── 📦 <b>Секция</b> (Точнее? Например: "Банка №4")
        </pre>

        <h3>💡 Важные советы</h3>
        <ul>
            <li><b>Единый стандарт:</b> Не называйте одно и то же место по-разному. Если есть "Шкаф", не пишите "Шкафчик".</li>
            <li><b>Не пропускайте уровни:</b> Если деталь лежит просто на столе, адрес будет: <code>Офис / Стол</code>. Не оставляйте поля пустыми посередине.</li>
            <li><b>Прикрепляйте фото:</b> Если у вас есть похожие микросхемы, сделайте фото и приложите к карточке детали. Это сэкономит массу нервов.</li>
        </ul>
        """

    def _get_signals_text(self):
        return """
        <h2>🎨 Язык цветов (Индикация)</h2>
        <p>Программа "подсвечивает" проблемы, чтобы вы их сразу заметили.</p>
        
        <h3>1. Фоновый цвет строки (Количество)</h3>
        <p>Говорит о том, <b>сколько</b> деталей осталось:</p>
        <table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%;">
            <tr>
                <td style="background-color: #c8e6c9; font-weight: bold; color: #000000;">🟢 Зелёный</td>
                <td><b>Всё отлично.</b> Деталей много (> 10 шт). Можно не беспокоиться.</td>
            </tr>
            <tr>
                <td style="background-color: #fff9c4; font-weight: bold; color: #000000;">🟡 Жёлтый</td>
                <td><b>Внимание!</b> Запасы на исходе (1-9 шт). Пора планировать закупку.</td>
            </tr>
            <tr>
                <td style="background-color: #ffcdd2; font-weight: bold; color: #000000;">🔴 Красный</td>
                <td><b>Тревога!</b> Деталей нет (0 шт). Срочно в магазин/на AliExpress.</td>
            </tr>
        </table>
        
        <h3>2. Цвет бейджа "Состояние"</h3>
        <p>Говорит о <b>качестве</b> детали:</p>
        <ul>
            <li>🟢 <b>Зелёный:</b> Новое / Отличное / Проверенное.</li>
            <li>🔵 <b>Голубой:</b> Б/У проверено.</li>
            <li>🟡 <b>Жёлтый:</b> Б/У (требует проверки).</li>
            <li>🔴 <b>Красный:</b> Неисправно / Брак.</li>
        </ul>
        
        <p style="color: gray; font-size: 10pt; text-align: right;">Система визуальных подсказок v1.0</p>
        """