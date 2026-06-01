"""Просмотрщик HTTP-запроса и ответа."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTextEdit, QLabel,
    QHBoxLayout, QPushButton, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from proxy.models import HttpMessage


class RequestViewer(QWidget):
    """Просмотрщик запроса и ответа с подсветкой."""
    
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Заголовок
        self.title_label = QLabel("Select a request from history")
        self.title_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #2d2d2d;
                color: #ff6600;
                font-weight: bold;
                font-size: 13px;
                border-bottom: 1px solid #3c3c3c;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Спойлер: Request / Response
        self.tabs = QTabWidget()
        
        # Вкладка Request
        self.request_view = QTextEdit()
        self.request_view.setReadOnly(True)
        self.request_view.setFont(QFont("Consolas", 11))
        self.request_view.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
            }
        """)
        self.tabs.addTab(self.request_view, "Request")
        
        # Вкладка Response
        self.response_view = QTextEdit()
        self.response_view.setReadOnly(True)
        self.response_view.setFont(QFont("Consolas", 11))
        self.response_view.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
            }
        """)
        self.tabs.addTab(self.response_view, "Response")
        
        layout.addWidget(self.tabs)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(5, 5, 5, 5)
        
        self.send_to_repeater_btn = QPushButton("Send to Repeater")
        self.send_to_repeater_btn.setStyleSheet("""
            QPushButton {
                background-color: #094771;
                color: white;
                padding: 6px 12px;
                border: 1px solid #0d6efd;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #0d5a8a;
            }
        """)
        btn_layout.addWidget(self.send_to_repeater_btn)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
    
    def show_message(self, msg: HttpMessage):
        """Отображает HTTP-сообщение."""
        
        self.title_label.setText(
            f"#{msg.id} {msg.method} {msg.url} [{msg.state.value}]"
        )
        
        # Формируем запрос
        request_text = self._format_request(msg)
        self.request_view.setText(request_text)
        
        # Формируем ответ
        response_text = self._format_response(msg)
        self.response_view.setText(response_text)
        
        # Переключаем на Request
        self.tabs.setCurrentIndex(0)
    
    def _format_request(self, msg: HttpMessage) -> str:
        """Форматирует запрос для отображения."""
        lines = []
        
        # Request line
        lines.append(f"{msg.method} {msg.path} HTTP/1.1")
        
        # Headers
        for key, value in msg.request_headers.items():
            lines.append(f"{key}: {value}")
        
        lines.append("")
        
        # Body
        if msg.request_body:
            body_text = msg.get_request_body_as_text()
            lines.append(msg.try_format_json(body_text))
        
        return "\n".join(lines)
    
    def _format_response(self, msg: HttpMessage) -> str:
        """Форматирует ответ для отображения."""
        lines = []
        
        if msg.status_code:
            # Status line
            reason = msg.reason_phrase or ""
            lines.append(f"HTTP/1.1 {msg.status_code} {reason}")
            
            # Headers
            for key, value in msg.response_headers.items():
                lines.append(f"{key}: {value}")
            
            lines.append("")
            
            # Body
            if msg.response_body:
                body_text = msg.get_response_body_as_text()
                lines.append(msg.try_format_json(body_text))
        else:
            lines.append("No response yet")
        
        return "\n".join(lines)
    
    def clear(self):
        """Очищает просмотрщик."""
        self.title_label.setText("Select a request from history")
        self.request_view.clear()
        self.response_view.clear()