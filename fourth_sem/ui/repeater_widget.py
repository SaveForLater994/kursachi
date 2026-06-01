"""Repeater — ручная отправка и модификация HTTP-запросов."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QSplitter, QComboBox, QLineEdit,
    QTabWidget, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from proxy.models import HttpMessage
from proxy.http_client import HttpClient

import json


class RequestSender(QThread):
    """Отправляет HTTP-запрос в отдельном потоке."""
    
    response_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, method: str, url: str, headers: dict, body: bytes):
        super().__init__()
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
    
    def run(self):
        try:
            client = HttpClient(timeout=30)
            result = client.send(
                method=self.method,
                url=self.url,
                headers=self.headers,
                body=self.body,
            )
            
            if result.get("error"):
                self.error_occurred.emit(result["error"])
            else:
                self.response_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class RepeaterWidget(QWidget):
    """Вкладка Repeater для ручной отправки запросов."""
    
    def __init__(self):
        super().__init__()
        
        # Кэш для хранения сырых данных ответа
        self._response_data: dict | None = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # --- Панель запроса ---
        request_group = QGroupBox("Request")
        request_layout = QVBoxLayout(request_group)
        
        # Строка: Method + URL + Send
        control_layout = QHBoxLayout()
        
        # Method
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "GET", "POST", "PUT", "DELETE", "PATCH", 
            "HEAD", "OPTIONS", "TRACE"
        ])
        self.method_combo.setFixedWidth(90)
        self.method_combo.setFont(QFont("Consolas", 11))
        control_layout.addWidget(self.method_combo)
        
        # URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/api/endpoint")
        self.url_input.setFont(QFont("Consolas", 11))
        control_layout.addWidget(self.url_input, stretch=1)
        
        # Send button
        self.send_btn = QPushButton("▶ Send")
        self.send_btn.setObjectName("forwardBtn")
        self.send_btn.setMinimumWidth(100)
        self.send_btn.setMinimumHeight(35)
        self.send_btn.clicked.connect(self._send_request)
        control_layout.addWidget(self.send_btn)
        
        request_layout.addLayout(control_layout)
        
        # Редактор запроса с вкладками
        self.request_tabs = QTabWidget()
        
        # Pretty (форматированный JSON/XML)
        self.request_pretty = QTextEdit()
        self.request_pretty.setFont(QFont("Consolas", 12))
        self.request_pretty.setPlaceholderText(
            "GET / HTTP/1.1\n"
            "Host: example.com\n"
            "User-Agent: BurpLite/1.0\n"
            "Accept: */*\n"
            "\n"
        )
        self.request_tabs.addTab(self.request_pretty, "Pretty")
        
        # Raw (сырой текст)
        self.request_raw = QTextEdit()
        self.request_raw.setFont(QFont("Consolas", 12))
        self.request_raw.setPlaceholderText("Raw HTTP request...")
        self.request_tabs.addTab(self.request_raw, "Raw")
        
        # Hex (шестнадцатеричный дамп)
        self.request_hex = QTextEdit()
        self.request_hex.setFont(QFont("Consolas", 12))
        self.request_hex.setReadOnly(True)
        self.request_hex.setPlaceholderText(
            "Hex dump will appear here\n"
            "Edit in Pretty or Raw tab"
        )
        self.request_tabs.addTab(self.request_hex, "Hex")
        
        # При переключении вкладок синхронизируем содержимое
        self.request_tabs.currentChanged.connect(self._sync_request_tabs)
        
        request_layout.addWidget(self.request_tabs)
        
        layout.addWidget(request_group)
        
        # --- Спойлер Request/Response ---
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Панель ответа
        response_group = QGroupBox("Response")
        response_layout = QVBoxLayout(response_group)
        
        # Статус ответа
        self.response_status = QLabel("")
        self.response_status.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
                background-color: #2d2d2d;
                border-radius: 3px;
            }
        """)
        response_layout.addWidget(self.response_status)
        
        # Вкладки ответа
        self.response_tabs = QTabWidget()
        
        # Pretty
        self.response_pretty = QTextEdit()
        self.response_pretty.setReadOnly(True)
        self.response_pretty.setFont(QFont("Consolas", 11))
        self.response_tabs.addTab(self.response_pretty, "Pretty")
        
        # Raw
        self.response_raw = QTextEdit()
        self.response_raw.setReadOnly(True)
        self.response_raw.setFont(QFont("Consolas", 11))
        self.response_tabs.addTab(self.response_raw, "Raw")
        
        # Headers
        self.response_headers = QTextEdit()
        self.response_headers.setReadOnly(True)
        self.response_headers.setFont(QFont("Consolas", 11))
        self.response_tabs.addTab(self.response_headers, "Headers")
        
        # Hex
        self.response_hex = QTextEdit()
        self.response_hex.setReadOnly(True)
        self.response_hex.setFont(QFont("Consolas", 12))
        self.response_tabs.addTab(self.response_hex, "Hex")
        
        response_layout.addWidget(self.response_tabs)
        
        splitter.addWidget(request_group)
        splitter.addWidget(response_group)
        splitter.setSizes([350, 450])
        
        layout.addWidget(splitter)
        
        # Счётчик запросов
        self.counter_label = QLabel("Requests sent: 0")
        self.counter_label.setStyleSheet("""
            QLabel {
                color: #888888;
                padding: 3px;
            }
        """)
        layout.addWidget(self.counter_label)
        
        self._request_count = 0
        self._sender_thread: RequestSender | None = None
    
    def _text_to_hexdump(self, text: str) -> str:
        """Преобразует текст в hex dump."""
        
        if not text:
            return ""
        
        data = text.encode("utf-8", errors="replace")
        lines = []
        
        for i in range(0, len(data), 16):
            chunk = data[i:i + 16]
            
            # Адрес (offset)
            offset = f"{i:08x}"
            
            # Hex значения
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            hex_part = hex_part.ljust(48)  # 16 байт * 3 символа
            
            # ASCII представление
            ascii_part = ""
            for b in chunk:
                if 32 <= b <= 126:
                    ascii_part += chr(b)
                else:
                    ascii_part += "."
            
            lines.append(f"{offset}  {hex_part}  |{ascii_part}|")
        
        return "\n".join(lines)
    
    def _format_body_pretty(self, body: bytes, content_type: str = "") -> str:
        """Форматирует тело ответа: JSON — pretty print, иначе как есть."""
        
        if not body:
            return ""
        
        try:
            text = body.decode("utf-8", errors="replace")
        except:
            return str(body)
        
        # Пробуем JSON
        if "json" in content_type.lower() or text.strip().startswith(("{", "[")):
            try:
                data = json.loads(text)
                return json.dumps(data, indent=2, ensure_ascii=False)
            except (json.JSONDecodeError, ValueError):
                pass
        
        return text
    
    def _sync_request_tabs(self, index: int):
        """Синхронизирует содержимое между вкладками запроса."""
        
        source = None
        
        if index == 0:  # Pretty
            source = self.request_pretty
        elif index == 1:  # Raw
            source = self.request_raw
        elif index == 2:  # Hex
            # Hex — только для просмотра, берём из Raw
            text = self.request_raw.toPlainText()
            self.request_hex.setText(self._text_to_hexdump(text))
            return
        
        if source:
            text = source.toPlainText()
            
            # Обновляем Pretty (если не он активен)
            if index != 0:
                self.request_pretty.blockSignals(True)
                cursor_pos = self.request_pretty.textCursor().position()
                self.request_pretty.setText(text)
                self.request_pretty.blockSignals(False)
            
            # Обновляем Raw (если не он активен)
            if index != 1:
                self.request_raw.blockSignals(True)
                self.request_raw.setText(text)
                self.request_raw.blockSignals(False)
            
            # Обновляем Hex (всегда)
            self.request_hex.setText(self._text_to_hexdump(text))
    
    def load_request(self, msg: HttpMessage):
        """Загружает перехваченный запрос в редактор."""
        
        # Метод и URL
        self.method_combo.setCurrentText(msg.method)
        self.url_input.setText(msg.url)
        
        # Формируем сырой запрос
        lines = [f"{msg.method} {msg.path} HTTP/1.1"]
        
        for key, value in msg.request_headers.items():
            if key.lower() not in ["content-length", "connection"]:
                lines.append(f"{key}: {value}")
            elif key.lower() == "host":
                lines.append(f"Host: {msg.host}")
        
        lines.append("")
        
        if msg.request_body:
            body_text = msg.get_request_body_as_text()
            lines.append(msg.try_format_json(body_text))
        
        raw_request = "\n".join(lines)
        
        # Заполняем все вкладки запроса
        self.request_pretty.setText(raw_request)
        self.request_raw.setText(raw_request)
        self.request_hex.setText(self._text_to_hexdump(raw_request))
        
        # Переключаем на Pretty
        self.request_tabs.setCurrentIndex(0)
    
    def _send_request(self):
        """Отправляет запрос."""
        
        method = self.method_combo.currentText()
        url = self.url_input.text().strip()
        
        if not url:
            self.response_status.setText("❌ URL is required")
            return
        
        # Берём текст из Raw вкладки
        raw_text = self.request_raw.toPlainText()
        headers, body = self._parse_raw_request(raw_text)
        
        # Отключаем кнопку
        self.send_btn.setEnabled(False)
        self.send_btn.setText("⏳ Sending...")
        
        # Отправляем в фоне
        self._sender_thread = RequestSender(
            method=method,
            url=url,
            headers=headers,
            body=body,
        )
        self._sender_thread.response_ready.connect(self._show_response)
        self._sender_thread.error_occurred.connect(self._show_error)
        self._sender_thread.start()
    
    def _parse_raw_request(self, raw: str) -> tuple[dict, bytes]:
        """Парсит сырой HTTP-запрос."""
        
        headers = {}
        body = b""
        
        lines = raw.split("\n")
        
        # Пропускаем request line
        start = 0
        if lines and " " in lines[0]:
            start = 1
        
        # Ищем разделитель заголовков и тела
        body_start = -1
        for i, line in enumerate(lines[start:], start):
            if line.strip() == "":
                body_start = i + 1
                break
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        
        if body_start > 0 and body_start < len(lines):
            body_text = "\n".join(lines[body_start:])
            body = body_text.encode("utf-8")
        
        return headers, body
    
    def _show_response(self, result: dict):
        """Отображает ответ."""
        
        self.send_btn.setEnabled(True)
        self.send_btn.setText("▶ Send")
        
        self._request_count += 1
        self.counter_label.setText(f"Requests sent: {self._request_count}")
        
        self._response_data = result
        
        # Статус
        status = result["status_code"]
        reason = result.get("reason", "")
        elapsed = result.get("elapsed_ms", 0)
        
        status_text = f"HTTP/1.1 {status} {reason}  |  {elapsed} ms"
        self.response_status.setText(status_text)
        
        if status < 300:
            self.response_status.setStyleSheet("""
                QLabel {
                    font-size: 14px; font-weight: bold; padding: 5px;
                    background-color: #1a3a1a; color: #49cc90;
                    border-radius: 3px;
                }
            """)
        elif status < 400:
            self.response_status.setStyleSheet("""
                QLabel {
                    font-size: 14px; font-weight: bold; padding: 5px;
                    background-color: #3a3a1a; color: #fca130;
                    border-radius: 3px;
                }
            """)
        else:
            self.response_status.setStyleSheet("""
                QLabel {
                    font-size: 14px; font-weight: bold; padding: 5px;
                    background-color: #3a1a1a; color: #f93e3e;
                    border-radius: 3px;
                }
            """)
        
        # Определяем Content-Type
        content_type = ""
        for key, value in result["headers"].items():
            if key.lower() == "content-type":
                content_type = value
                break
        
        # --- Pretty (форматированное тело) ---
        if result["body"]:
            pretty_text = self._format_body_pretty(result["body"], content_type)
        else:
            pretty_text = ""
        self.response_pretty.setText(pretty_text)
        
        # --- Raw (полный ответ) ---
        raw_lines = [f"HTTP/1.1 {status} {reason}"]
        for key, value in result["headers"].items():
            raw_lines.append(f"{key}: {value}")
        raw_lines.append("")
        
        if result["body"]:
            try:
                raw_lines.append(result["body"].decode("utf-8", errors="replace"))
            except:
                raw_lines.append(str(result["body"]))
        
        raw_text = "\n".join(raw_lines)
        self.response_raw.setText(raw_text)
        
        # --- Headers ---
        headers_text = "\n".join(
            f"{key}: {value}" for key, value in result["headers"].items()
        )
        self.response_headers.setText(headers_text)
        
        # --- Hex ---
        self.response_hex.setText(self._text_to_hexdump(raw_text))
        
        # Переключаем на Pretty
        self.response_tabs.setCurrentIndex(0)
    
    def _show_error(self, error: str):
        """Показывает ошибку."""
        
        self.send_btn.setEnabled(True)
        self.send_btn.setText("▶ Send")
        
        self._response_data = None
        
        self.response_status.setText(f"❌ {error}")
        self.response_status.setStyleSheet("""
            QLabel {
                font-size: 14px; font-weight: bold; padding: 5px;
                background-color: #3a1a1a; color: #f93e3e;
                border-radius: 3px;
            }
        """)
        
        self.response_pretty.setText(f"Error: {error}")
        self.response_raw.setText(f"Error: {error}")
        self.response_headers.clear()
        self.response_hex.setText(self._text_to_hexdump(f"Error: {error}"))