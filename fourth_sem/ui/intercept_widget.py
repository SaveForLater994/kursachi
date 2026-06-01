"""Виджет перехвата запросов (как в Burp Suite)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from proxy.models import HttpMessage
from proxy.interceptor import Interceptor


class InterceptWidget(QWidget):
    """Виджет для перехвата и модификации запросов."""
    
    # Сигналы
    request_forwarded = pyqtSignal(int)  # msg_id
    request_dropped = pyqtSignal(int)
    
    def __init__(self, interceptor: Interceptor):
        super().__init__()
        
        self.interceptor = interceptor
        self._current_msg: HttpMessage | None = None
        self._checking = False  # Защита от рекурсии
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок
        title_layout = QHBoxLayout()
        
        self.title_label = QLabel("Intercept is OFF")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ff6600;
                padding: 5px;
            }
        """)
        title_layout.addWidget(self.title_label)
        
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Редактор запроса
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.editor.setPlaceholderText(
            "Intercepted request will appear here...\n\n"
            "Enable Intercept to capture requests."
        )
        layout.addWidget(self.editor)
        
        # Кнопки Forward / Drop
        btn_layout = QHBoxLayout()
        
        self.forward_btn = QPushButton("▶ Forward")
        self.forward_btn.setObjectName("forwardBtn")
        self.forward_btn.setMinimumHeight(40)
        self.forward_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.forward_btn.clicked.connect(self._on_forward)
        self.forward_btn.setEnabled(False)
        btn_layout.addWidget(self.forward_btn)
        
        self.drop_btn = QPushButton("⏹ Drop")
        self.drop_btn.setObjectName("dropBtn")
        self.drop_btn.setMinimumHeight(40)
        self.drop_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.drop_btn.clicked.connect(self._on_drop)
        self.drop_btn.setEnabled(False)
        btn_layout.addWidget(self.drop_btn)
        
        layout.addLayout(btn_layout)
        
        # Таймер для проверки очереди
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._check_queue)
        self._check_timer.start(200)  # Проверяем каждые 200 мс
    
    def _check_queue(self):
        """Проверяет очередь перехваченных запросов."""
        
        # Защита от рекурсии
        if self._checking:
            return
        
        if not self.interceptor.intercept_enabled:
            return
        
        if self._current_msg is None:
            self._checking = True
            
            try:
                msg = self.interceptor.poll_intercepted()
                
                if msg:
                    self._current_msg = msg
                    self._show_request(msg)
            finally:
                self._checking = False
    
    def _show_request(self, msg: HttpMessage):
        """Показывает перехваченный запрос."""
        
        # Форматируем запрос
        lines = [f"{msg.method} {msg.path} HTTP/1.1"]
        
        for key, value in msg.request_headers.items():
            lines.append(f"{key}: {value}")
        
        lines.append("")
        
        if msg.request_body:
            body_text = msg.get_request_body_as_text()
            lines.append(msg.try_format_json(body_text))
        
        self.editor.setText("\n".join(lines))
        
        self.title_label.setText(f"Intercepted: {msg.method} {msg.url}")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #28a745;
                padding: 5px;
            }
        """)
        
        self.forward_btn.setEnabled(True)
        self.drop_btn.setEnabled(True)
    
    def _on_forward(self):
        """Отправляет запрос дальше."""
        
        if self._current_msg:
            # Применяем изменения из редактора
            self._apply_edits()
            
            self.interceptor.forward(self._current_msg.id)
            self.request_forwarded.emit(self._current_msg.id)
            
            self._clear()
    
    def _on_drop(self):
        """Сбрасывает запрос."""
        
        if self._current_msg:
            self.interceptor.drop(self._current_msg.id)
            self.request_dropped.emit(self._current_msg.id)
            
            self._clear()
    
    def _apply_edits(self):
        """Применяет изменения из редактора к сообщению."""
        
        if not self._current_msg:
            return
        
        text = self.editor.toPlainText()
        lines = text.split("\n")
        
        if not lines:
            return
        
        # Парсим request line
        request_line = lines[0].strip().split(" ")
        if len(request_line) >= 2:
            self._current_msg.method = request_line[0]
            self._current_msg.path = request_line[1]
        
        # Парсим заголовки и тело
        headers = {}
        body_start = -1
        
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "":
                body_start = i + 1
                break
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        
        self._current_msg.request_headers = headers
        
        if body_start > 0 and body_start < len(lines):
            body_text = "\n".join(lines[body_start:])
            self._current_msg.request_body = body_text.encode("utf-8")
    
    def _clear(self):
        """Очищает виджет."""
        self._current_msg = None
        self.editor.clear()
        self.editor.setPlaceholderText(
            "Waiting for intercepted request...\n\n"
            "Enable Intercept to capture requests."
        )
        
        self.title_label.setText("Intercept is ON")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #28a745;
                padding: 5px;
            }
        """)
        
        self.forward_btn.setEnabled(False)
        self.drop_btn.setEnabled(False)
    
    def set_intercept_enabled(self, enabled: bool):
        """Обновляет состояние виджета."""
        
        if enabled:
            self.title_label.setText("Intercept is ON")
            self.title_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #28a745;
                    padding: 5px;
                }
            """)
        else:
            self.title_label.setText("Intercept is OFF")
            self.title_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #ff6600;
                    padding: 5px;
                }
            """)
            self._clear()