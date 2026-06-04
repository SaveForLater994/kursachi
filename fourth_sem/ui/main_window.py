"""Главное окно Burp Lite."""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QSplitter, QStatusBar,
    QToolBar, QMenuBar, QMenu, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon

from proxy.proxy_server import ProxyServer
from proxy.cert_manager import CertManager

from .styles import DARK_THEME
from .proxy_tab import ProxyTab
from .intercept_widget import InterceptWidget
from .history_table import HistoryTable
from .request_viewer import RequestViewer
from .repeater_widget import RepeaterWidget
from .decoder_widget import DecoderWidget  # ← НОВЫЙ ИМПОРТ

from pathlib import Path


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        
        # Прокси-сервер
        self.proxy = ProxyServer(port=8080)
        
        # Настройка окна
        self.setWindowTitle("Burp Lite - HTTP/HTTPS Proxy")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Применяем тёмную тему
        self.setStyleSheet(DARK_THEME)
        
        # Строим интерфейс
        self._setup_menu()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_statusbar()
        
        # Подключаем обработчики прокси
        self._connect_proxy_handlers()
        
        # Таймер обновления статус-бара
        self._stats_timer = QTimer()
        self._stats_timer.timeout.connect(self._update_stats)
        self._stats_timer.start(1000)
    
    def _setup_menu(self):
        """Создаёт меню."""
        
        menubar = self.menuBar()
        
        # File
        file_menu = menubar.addMenu("&File")
        
        export_ca_action = QAction("Export CA Certificate...", self)
        export_ca_action.triggered.connect(self._export_ca_cert)
        file_menu.addAction(export_ca_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View
        view_menu = menubar.addMenu("&View")
        
        clear_history_action = QAction("Clear History", self)
        clear_history_action.triggered.connect(self._clear_history)
        view_menu.addAction(clear_history_action)
        
        # Help
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("About Burp Lite", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        ca_help_action = QAction("CA Certificate Help", self)
        ca_help_action.triggered.connect(self._show_ca_help)
        help_menu.addAction(ca_help_action)
    
    def _setup_toolbar(self):
        """Создаёт тулбар."""
        
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Кнопка перехвата
        self.intercept_toolbar_btn = QAction("⏺ Intercept", self)
        self.intercept_toolbar_btn.setCheckable(True)
        self.intercept_toolbar_btn.triggered.connect(self._toolbar_intercept_toggle)
        toolbar.addAction(self.intercept_toolbar_btn)
    
    def _setup_central_widget(self):
        """Создаёт центральный виджет с вкладками."""
        
        self.tabs = QTabWidget()
        
        # --- Вкладка Proxy ---
        proxy_splitter = QSplitter(Qt.Orientation.Vertical)
        
        self.intercept_widget = InterceptWidget(self.proxy.interceptor)
        proxy_splitter.addWidget(self.intercept_widget)
        
        history_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.history_table = HistoryTable()
        history_splitter.addWidget(self.history_table)
        
        self.request_viewer = RequestViewer()
        history_splitter.addWidget(self.request_viewer)
        
        history_splitter.setSizes([700, 500])
        
        proxy_splitter.addWidget(history_splitter)
        proxy_splitter.setSizes([250, 550])
        
        self.tabs.addTab(proxy_splitter, "🔍 Proxy")
        
        # --- Вкладка Repeater ---
        self.repeater_widget = RepeaterWidget()
        self.tabs.addTab(self.repeater_widget, "📤 Repeater")
        
        # --- Вкладка Decoder (НОВАЯ) ---
        self.decoder_widget = DecoderWidget()
        self.tabs.addTab(self.decoder_widget, "🔧 Decoder")
        
        # --- Вкладка Settings ---
        self.proxy_tab = ProxyTab(self.proxy)
        self.tabs.addTab(self.proxy_tab, "⚙ Settings")
        
        self.setCentralWidget(self.tabs)
    
    def _setup_statusbar(self):
        """Создаёт статус-бар."""
        
        self.statusbar = QStatusBar()
        self.statusbar.showMessage("Ready | Proxy: 127.0.0.1:8080 | Intercept: OFF")
        self.setStatusBar(self.statusbar)
    
    def _connect_proxy_handlers(self):
        """Подключает обработчики событий прокси."""
        
        self.proxy.interceptor.on_request_captured = self.history_table.add_request
        self.proxy.interceptor.on_response_received = self.history_table.update_response
        
        self.history_table.request_selected.connect(self.request_viewer.show_message)
        self.history_table.open_in_repeater.connect(self._open_in_repeater)
        
        self.request_viewer.send_to_repeater_btn.clicked.connect(
            self._send_current_to_repeater
        )
        
        self.proxy_tab.intercept_toggled.connect(self._on_intercept_toggled)
        
        self.intercept_widget.request_forwarded.connect(self._on_request_forwarded)
        self.intercept_widget.request_dropped.connect(self._on_request_dropped)
    
    def _open_in_repeater(self, msg):
        """Открывает запрос в Repeater."""
        
        self.repeater_widget.load_request(msg)
        self.tabs.setCurrentWidget(self.repeater_widget)
    
    def _send_current_to_repeater(self):
        """Отправляет текущий выбранный запрос в Repeater."""
        
        msg = self.history_table.get_selected_message()
        if msg:
            self._open_in_repeater(msg)
    
    def _toolbar_intercept_toggle(self):
        """Переключает режим перехвата из тулбара."""
        
        enabled = self.proxy.toggle_intercept()
        self.intercept_widget.set_intercept_enabled(enabled)
        self.proxy_tab.intercept_btn.setChecked(enabled)
        
        if enabled:
            self.intercept_toolbar_btn.setText("⏺ Intercept ON")
        else:
            self.intercept_toolbar_btn.setText("⏺ Intercept OFF")
    
    def _on_intercept_toggled(self, enabled: bool):
        """Обработчик переключения перехвата."""
        
        self.intercept_widget.set_intercept_enabled(enabled)
        
        if enabled:
            self.intercept_toolbar_btn.setText("⏺ Intercept ON")
        else:
            self.intercept_toolbar_btn.setText("⏺ Intercept OFF")
    
    def _on_request_forwarded(self, msg_id: int):
        """Запрос отправлен."""
        self.statusbar.showMessage(f"Request #{msg_id} forwarded | Intercept: ON")
    
    def _on_request_dropped(self, msg_id: int):
        """Запрос сброшен."""
        self.statusbar.showMessage(f"Request #{msg_id} dropped | Intercept: ON")
    
    def _update_stats(self):
        """Обновляет статистику в статус-баре."""
        
        if self.proxy.is_running:
            history_count = self.history_table.rowCount()
            intercept_status = "ON" if self.proxy.interceptor.intercept_enabled else "OFF"
            
            self.statusbar.showMessage(
                f"Proxy: {self.proxy.proxy_url} | "
                f"Requests: {history_count} | "
                f"Intercept: {intercept_status}"
            )
    
    def _export_ca_cert(self):
        """Экспортирует CA сертификат."""
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CA Certificate",
            str(Path.home() / "burplite-ca.pem"),
            "Certificate Files (*.pem *.crt *.cer);;All Files (*)"
        )
        
        if file_path:
            try:
                CertManager.export_ca_cert(Path(file_path))
                QMessageBox.information(
                    self,
                    "Success",
                    f"CA certificate exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to export certificate:\n{e}"
                )
    
    def _clear_history(self):
        """Очищает историю запросов."""
        
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_table.clear_history()
            self.proxy.interceptor.clear_history()
            self.request_viewer.clear()
    
    def _show_about(self):
        """Показывает окно About."""
        
        QMessageBox.about(
            self,
            "About Burp Lite",
            "<h2>Burp Lite v1.0</h2>"
            "<p>Облегчённый аналог Burp Suite</p>"
            "<p>Курсовая работа</p>"
            "<hr>"
            "<p>Возможности:</p>"
            "<ul>"
            "<li>HTTP/HTTPS прокси-сервер</li>"
            "<li>Перехват и модификация запросов</li>"
            "<li>Repeater для повторной отправки</li>"
            "<li>Encoder/Decoder (URL, Base64, Hex, HTML)</li>"
            "<li>История всех запросов</li>"
            "</ul>"
        )
    
    def _show_ca_help(self):
        """Показывает справку по установке CA."""
        
        help_text = CertManager.get_firefox_instructions()
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("CA Certificate Installation")
        msg_box.setText("How to install CA certificate in Firefox:")
        msg_box.setDetailedText(help_text)
        msg_box.exec()
    
    def closeEvent(self, event):
        """Обработчик закрытия окна."""
        
        if self.proxy.is_running:
            reply = QMessageBox.question(
                self,
                "Exit",
                "Proxy is still running. Stop and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.proxy.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()