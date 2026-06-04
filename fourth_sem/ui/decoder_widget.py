"""Encoder/Decoder — кодирование и декодирование текста."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QComboBox, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import urllib.parse
import base64
import html
import binascii


class DecoderWidget(QWidget):
    """Вкладка Encoder/Decoder для работы с текстом."""
    
    # Доступные операции
    OPERATIONS = {
        "URL Encode": {
            "encode": lambda text: urllib.parse.quote(text, safe=""),
            "encode_all": lambda text: urllib.parse.quote(text, safe=""),
            "description": "URL-кодирование (%20, %3C и т.д.)"
        },
        "URL Decode": {
            "encode": lambda text: urllib.parse.unquote(text),
            "description": "Декодирование URL (%20 → пробел)"
        },
        "Base64 Encode": {
            "encode": lambda text: base64.b64encode(text.encode("utf-8")).decode("utf-8"),
            "description": "Кодирование в Base64"
        },
        "Base64 Decode": {
            "encode": lambda text: base64.b64decode(text.encode("utf-8")).decode("utf-8", errors="replace"),
            "description": "Декодирование из Base64"
        },
        "HTML Entity Encode": {
            "encode": lambda text: html.escape(text),
            "description": "HTML-кодирование (&lt; &gt; &amp;)"
        },
        "HTML Entity Decode": {
            "encode": lambda text: html.unescape(text),
            "description": "HTML-декодирование"
        },
        "Hex Encode": {
            "encode": lambda text: text.encode("utf-8").hex(),
            "description": "Шестнадцатеричное кодирование"
        },
        "Hex Decode": {
            "encode": lambda text: bytes.fromhex(text).decode("utf-8", errors="replace"),
            "description": "Декодирование из hex"
        },
        "Binary Encode": {
            "encode": lambda text: " ".join(format(ord(c), "08b") for c in text),
            "description": "Бинарное представление"
        },
        "Binary Decode": {
            "encode": lambda text: "".join(chr(int(b, 2)) for b in text.split()),
            "description": "Декодирование из бинарного вида"
        },
        "MD5 Hash": {
            "encode": lambda text: __import__("hashlib").md5(text.encode()).hexdigest(),
            "description": "MD5 хеш (необратимо)"
        },
        "SHA256 Hash": {
            "encode": lambda text: __import__("hashlib").sha256(text.encode()).hexdigest(),
            "description": "SHA-256 хеш (необратимо)"
        },
    }
    
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок
        title = QLabel("Encoder / Decoder")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ff6600;
                padding: 5px;
            }
        """)
        layout.addWidget(title)
        
        # --- Панель управления ---
        control_layout = QHBoxLayout()
        
        # Выбор операции
        control_layout.addWidget(QLabel("Operation:"))
        
        self.operation_combo = QComboBox()
        self.operation_combo.setFont(QFont("Consolas", 11))
        self.operation_combo.addItems(self.OPERATIONS.keys())
        self.operation_combo.setMinimumWidth(200)
        self.operation_combo.currentTextChanged.connect(self._on_operation_changed)
        control_layout.addWidget(self.operation_combo)
        
        control_layout.addStretch()
        
        # Кнопки
        self.encode_btn = QPushButton("▶ Encode / Decode")
        self.encode_btn.setObjectName("forwardBtn")
        self.encode_btn.setMinimumHeight(35)
        self.encode_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.encode_btn.clicked.connect(self._process_text)
        control_layout.addWidget(self.encode_btn)
        
        self.swap_btn = QPushButton("⇅ Swap")
        self.swap_btn.setMinimumHeight(35)
        self.swap_btn.clicked.connect(self._swap_text)
        control_layout.addWidget(self.swap_btn)
        
        layout.addLayout(control_layout)
        
        # Описание операции
        self.description_label = QLabel("")
        self.description_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-style: italic;
                padding: 3px;
            }
        """)
        layout.addWidget(self.description_label)
        
        # --- Редакторы ---
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Входные данные
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout(input_group)
        
        self.input_text = QTextEdit()
        self.input_text.setFont(QFont("Consolas", 12))
        self.input_text.setPlaceholderText("Enter text to encode/decode...")
        input_layout.addWidget(self.input_text)
        
        splitter.addWidget(input_group)
        
        # Выходные данные
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout(output_group)
        
        self.output_text = QTextEdit()
        self.output_text.setFont(QFont("Consolas", 12))
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Result will appear here...")
        output_layout.addWidget(self.output_text)
        
        splitter.addWidget(output_group)
        splitter.setSizes([300, 300])
        
        layout.addWidget(splitter)
        
        # --- Статистика ---
        stats_layout = QHBoxLayout()
        
        self.input_length_label = QLabel("Input: 0 chars")
        self.input_length_label.setStyleSheet("color: #888888;")
        stats_layout.addWidget(self.input_length_label)
        
        self.output_length_label = QLabel("Output: 0 chars")
        self.output_length_label.setStyleSheet("color: #888888;")
        stats_layout.addWidget(self.output_length_label)
        
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        # Обновляем при вводе
        self.input_text.textChanged.connect(self._update_stats)
        
        # Загружаем описание первой операции
        self._on_operation_changed(self.operation_combo.currentText())
    
    def _on_operation_changed(self, operation_name: str):
        """Обновляет описание операции."""
        
        op = self.OPERATIONS.get(operation_name, {})
        self.description_label.setText(op.get("description", ""))
    
    def _process_text(self):
        """Выполняет кодирование/декодирование."""
        
        input_text = self.input_text.toPlainText()
        
        if not input_text:
            self.output_text.setText("")
            return
        
        operation_name = self.operation_combo.currentText()
        op = self.OPERATIONS.get(operation_name, {})
        
        if "encode" not in op:
            self.output_text.setText(f"Unknown operation: {operation_name}")
            return
        
        try:
            result = op["encode"](input_text)
            self.output_text.setText(result)
            
            # Меняем цвет в зависимости от успеха
            self.output_text.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #49cc90;
                    border: 1px solid #3c3c3c;
                }
            """)
            
        except Exception as e:
            self.output_text.setText(f"Error: {e}")
            self.output_text.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #f93e3e;
                    border: 1px solid #f93e3e;
                }
            """)
        
        self._update_stats()
    
    def _swap_text(self):
        """Меняет местами input и output."""
        
        output = self.output_text.toPlainText()
        input_text = self.input_text.toPlainText()
        
        self.input_text.setText(output)
        self.output_text.setText(input_text)
        
        self._process_text()
    
    def _update_stats(self):
        """Обновляет статистику длин."""
        
        input_len = len(self.input_text.toPlainText())
        output_len = len(self.output_text.toPlainText())
        
        self.input_length_label.setText(f"Input: {input_len} chars")
        self.output_length_label.setText(f"Output: {output_len} chars")
    
    def set_input_text(self, text: str):
        """Устанавливает текст для кодирования (вызов извне)."""
        
        self.input_text.setText(text)
        self._process_text()