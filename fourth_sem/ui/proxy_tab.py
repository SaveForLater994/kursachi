"""Вкладка управления прокси-сервером."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSpinBox, QGroupBox, QFormLayout,
    QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from proxy.proxy_server import ProxyServer


class ProxyTab(QWidget):
    """Вкладка управления прокси."""
    
    # Сигналы
    proxy_started = pyqtSignal(int)  # port
    proxy_stopped = pyqtSignal()
    intercept_toggled = pyqtSignal(bool)  # enabled
    
    def __init__(self, proxy_server: ProxyServer):
        super().__init__()
        
        self.proxy = proxy_server
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # --- Настройки прокси ---
        settings_group = QGroupBox("Proxy Settings")
        form = QFormLayout(settings_group)
        
        # Порт
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(8080)
        self.port_spin.setFont(QFont("Consolas", 12))
        form.addRow("Port:", self.port_spin)
        
        # Кнопка Start/Stop
        self.start_stop_btn = QPushButton("▶ Start Proxy")
        self.start_stop_btn.setMinimumHeight(40)
        self.start_stop_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.start_stop_btn.clicked.connect(self._toggle_proxy)
        form.addRow(self.start_stop_btn)
        
        # Статус
        self.status_label = QLabel("● Stopped")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #dc3545;
                padding: 5px;
            }
        """)
        form.addRow("Status:", self.status_label)
        
        layout.addWidget(settings_group)
        
        # --- Режим перехвата ---
        intercept_group = QGroupBox("Intercept")
        intercept_layout = QVBoxLayout(intercept_group)
        
        self.intercept_btn = QPushButton("⏺ Intercept is OFF")
        self.intercept_btn.setObjectName("interceptBtn")
        self.intercept_btn.setMinimumHeight(50)
        self.intercept_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.intercept_btn.setCheckable(True)
        self.intercept_btn.clicked.connect(self._toggle_intercept)
        intercept_layout.addWidget(self.intercept_btn)
        
        layout.addWidget(intercept_group)
        
        # --- Инструкция ---
        help_group = QGroupBox("Browser Configuration")
        help_layout = QVBoxLayout(help_group)
        
        self.help_text = QTextEdit()
        self.help_text.setReadOnly(True)
        self.help_text.setMaximumHeight(200)
        self.help_text.setFont(QFont("Consolas", 10))
        self.help_text.setText(
            "1. Set browser proxy:\n"
            "   HTTP Proxy: 127.0.0.1\n"
            "   Port: 8080\n\n"
            "2. Install CA certificate:\n"
            "   File → Export CA Certificate\n"
            "   Import in browser settings\n\n"
            "3. Quick install:\n"
            "   Open http://mitm.it in browser\n"
            "   (while proxy is running)"
        )
        help_layout.addWidget(self.help_text)
        
        layout.addWidget(help_group)
        
        layout.addStretch()
    
    def _toggle_proxy(self):
        """Запускает или останавливает прокси."""
        
        if self.proxy.is_running:
            self.proxy.stop()
            self.start_stop_btn.setText("▶ Start Proxy")
            self.start_stop_btn.setStyleSheet("")
            self.status_label.setText("● Stopped")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 14px; font-weight: bold;
                    color: #dc3545; padding: 5px;
                }
            """)
            self.proxy_stopped.emit()
        else:
            port = self.port_spin.value()
            self.proxy.port = port
            
            try:
                self.proxy.start()
                
                self.start_stop_btn.setText("⏹ Stop Proxy")
                self.start_stop_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border-color: #dc3545;
                    }
                    QPushButton:hover {
                        background-color: #e74c3c;
                    }
                """)
                
                self.status_label.setText(f"● Running on 127.0.0.1:{port}")
                self.status_label.setStyleSheet("""
                    QLabel {
                        font-size: 14px; font-weight: bold;
                        color: #28a745; padding: 5px;
                    }
                """)
                
                self.proxy_started.emit(port)
                
            except Exception as e:
                self.status_label.setText(f"● Error: {e}")
    
    def _toggle_intercept(self):
        """Переключает режим перехвата."""
        
        enabled = self.proxy.toggle_intercept()
        
        if enabled:
            self.intercept_btn.setText("⏺ Intercept is ON")
            self.intercept_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border-color: #28a745;
                    font-size: 14px;
                    padding: 8px 25px;
                }
            """)
        else:
            self.intercept_btn.setText("⏺ Intercept is OFF")
            self.intercept_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff6600;
                    color: white;
                    border-color: #ff6600;
                    font-size: 14px;
                    padding: 8px 25px;
                }
            """)
        
        self.intercept_toggled.emit(enabled)
    
    def update_status(self, message: str):
        """Обновляет статус."""
        self.status_label.setText(message)