"""Стили для Burp Lite в стиле Burp Suite."""

# Основная тёмная тема
DARK_THEME = """
QMainWindow {
    background-color: #1e1e1e;
    color: #d4d4d4;
}

QMenuBar {
    background-color: #2d2d2d;
    color: #cccccc;
    border-bottom: 1px solid #3c3c3c;
    padding: 2px;
}

QMenuBar::item:selected {
    background-color: #3c3c3c;
}

QMenu {
    background-color: #2d2d2d;
    color: #cccccc;
    border: 1px solid #3c3c3c;
}

QMenu::item:selected {
    background-color: #094771;
}

QToolBar {
    background-color: #252526;
    border-bottom: 1px solid #3c3c3c;
    spacing: 5px;
    padding: 3px;
}

QTabWidget::pane {
    border: 1px solid #3c3c3c;
    background-color: #1e1e1e;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #cccccc;
    padding: 8px 20px;
    border: 1px solid #3c3c3c;
    border-bottom: none;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
    border-bottom: 2px solid #ff6600;
    color: #ffffff;
}

QTabBar::tab:hover {
    background-color: #3c3c3c;
}

QStatusBar {
    background-color: #007acc;
    color: white;
    font-weight: bold;
    padding: 2px;
}

QSplitter::handle {
    background-color: #3c3c3c;
    width: 2px;
    height: 2px;
}

QGroupBox {
    color: #cccccc;
    border: 1px solid #3c3c3c;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QPushButton {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555555;
    padding: 6px 15px;
    border-radius: 3px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #4c4c4c;
    border-color: #ff6600;
}

QPushButton:pressed {
    background-color: #2c2c2c;
}

QPushButton:disabled {
    background-color: #2d2d2d;
    color: #666666;
}

QPushButton#forwardBtn {
    background-color: #28a745;
    color: white;
    border-color: #28a745;
}

QPushButton#forwardBtn:hover {
    background-color: #34ce57;
}

QPushButton#dropBtn {
    background-color: #dc3545;
    color: white;
    border-color: #dc3545;
}

QPushButton#dropBtn:hover {
    background-color: #e74c3c;
}

QPushButton#interceptBtn {
    background-color: #ff6600;
    color: white;
    border-color: #ff6600;
    font-size: 14px;
    padding: 8px 25px;
}

QPushButton#interceptBtn:checked {
    background-color: #28a745;
    border-color: #28a745;
}

QTableWidget {
    background-color: #252526;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    gridline-color: #3c3c3c;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}

QTableWidget::item {
    padding: 3px;
}

QTableWidget::item:selected {
    background-color: #094771;
    color: white;
}

QHeaderView::section {
    background-color: #2d2d2d;
    color: #cccccc;
    padding: 4px;
    border: 1px solid #3c3c3c;
    font-weight: bold;
}

QTextEdit, QPlainTextEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
    selection-background-color: #264f78;
}

QLineEdit {
    background-color: #3c3c3c;
    color: #d4d4d4;
    border: 1px solid #555555;
    padding: 5px;
    border-radius: 3px;
    font-family: 'Consolas', 'Courier New', monospace;
}

QLineEdit:focus {
    border-color: #ff6600;
}

QComboBox {
    background-color: #3c3c3c;
    color: #d4d4d4;
    border: 1px solid #555555;
    padding: 5px;
    border-radius: 3px;
}

QComboBox:hover {
    border-color: #ff6600;
}

QComboBox::drop-down {
    background-color: #2d2d2d;
    border-left: 1px solid #555555;
}

QSpinBox {
    background-color: #3c3c3c;
    color: #d4d4d4;
    border: 1px solid #555555;
    padding: 3px;
    border-radius: 3px;
}

QLabel {
    color: #cccccc;
}

QCheckBox {
    color: #cccccc;
}

QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #424242;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4f4f4f;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

# Стили для HTTP-методов (используются в HistoryTable)
METHOD_COLORS = {
    "GET": "#61affe",
    "POST": "#49cc90", 
    "PUT": "#fca130",
    "DELETE": "#f93e3e",
    "PATCH": "#50e3c2",
    "HEAD": "#9012fe",
    "OPTIONS": "#0d5aa7",
}

# Цвета для статус-кодов
STATUS_COLORS = {
    "2xx": "#49cc90",  # Success - зелёный
    "3xx": "#fca130",  # Redirect - оранжевый
    "4xx": "#f93e3e",  # Client Error - красный
    "5xx": "#ff6600",  # Server Error - тёмно-оранжевый
}