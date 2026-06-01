"""Таблица истории HTTP-запросов."""

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QBrush

from proxy.models import HttpMessage
from .styles import METHOD_COLORS, STATUS_COLORS


class HistoryTable(QTableWidget):
    """Таблица со списком всех перехваченных запросов."""
    
    # Сигнал: выбран запрос для просмотра
    request_selected = pyqtSignal(HttpMessage)
    
    # Сигнал: двойной клик — открыть в Repeater
    open_in_repeater = pyqtSignal(HttpMessage)
    
    COLUMNS = ["#", "Host", "Method", "Path", "Status", "Length", "Time"]
    
    def __init__(self):
        super().__init__()
        
        self.setColumnCount(len(self.COLUMNS))
        self.setHorizontalHeaderLabels(self.COLUMNS)
        
        # Настройка таблицы
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setShowGrid(True)
        
        # Растягиваем колонки
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        
        self.setColumnWidth(0, 50)
        self.setColumnWidth(2, 65)
        self.setColumnWidth(4, 60)
        self.setColumnWidth(5, 70)
        self.setColumnWidth(6, 60)
        
        # Вертикальный заголовок скрываем
        self.verticalHeader().setVisible(False)
        
        # Сигналы
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # Хранилище сообщений {request_id: HttpMessage}
        self._messages: dict[int, HttpMessage] = {}
        
        # Моноширинный шрифт
        self._mono_font = QFont("Consolas", 10)
    
    def add_request(self, msg: HttpMessage):
        """Добавляет новый запрос в таблицу."""
        self._messages[msg.id] = msg
        
        # Вставляем сверху
        self.insertRow(0)
        
        # ID
        id_item = QTableWidgetItem(str(msg.id))
        id_item.setFont(self._mono_font)
        self.setItem(0, 0, id_item)
        
        # Host
        self.setItem(0, 1, QTableWidgetItem(msg.host))
        
        # Method с цветом
        method_item = QTableWidgetItem(msg.method)
        method_item.setFont(self._mono_font)
        method_color = METHOD_COLORS.get(msg.method, "#999999")
        method_item.setForeground(QColor(method_color))
        method_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(0, 2, method_item)
        
        # Path
        path = msg.path
        if len(path) > 100:
            path = path[:97] + "..."
        self.setItem(0, 3, QTableWidgetItem(path))
        
        # Status (пока пусто)
        status_item = QTableWidgetItem("...")
        status_item.setFont(self._mono_font)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(0, 4, status_item)
        
        # Length
        length_item = QTableWidgetItem("0")
        length_item.setFont(self._mono_font)
        length_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(0, 5, length_item)
        
        # Time
        time_str = msg.timestamp.strftime("%H:%M:%S")
        time_item = QTableWidgetItem(time_str)
        time_item.setFont(self._mono_font)
        self.setItem(0, 6, time_item)
        
        # Автоскролл к новому
        self.scrollToTop()
    
    def update_response(self, msg: HttpMessage):
        """Обновляет строку с ответом (статус, длина)."""
        
        # Ищем строку по ID
        for row in range(self.rowCount()):
            id_item = self.item(row, 0)
            if id_item and int(id_item.text()) == msg.id:
                # Status
                status_item = QTableWidgetItem(str(msg.status_code))
                status_item.setFont(self._mono_font)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Цвет статуса
                status = msg.status_code
                if status < 300:
                    color = STATUS_COLORS["2xx"]
                elif status < 400:
                    color = STATUS_COLORS["3xx"]
                elif status < 500:
                    color = STATUS_COLORS["4xx"]
                else:
                    color = STATUS_COLORS["5xx"]
                
                status_item.setForeground(QColor(color))
                self.setItem(row, 4, status_item)
                
                # Length
                length = msg.response_length
                if length > 1024:
                    length_str = f"{length / 1024:.1f}K"
                else:
                    length_str = str(length)
                
                length_item = QTableWidgetItem(length_str)
                length_item.setFont(self._mono_font)
                length_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row, 5, length_item)
                
                # Обновляем сообщение
                self._messages[msg.id] = msg
                break
    
    def _on_item_clicked(self, item: QTableWidgetItem):
        """Обработчик клика по строке."""
        row = item.row()
        id_item = self.item(row, 0)
        
        if id_item:
            msg_id = int(id_item.text())
            msg = self._messages.get(msg_id)
            
            if msg:
                self.request_selected.emit(msg)
    
    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """Двойной клик — открыть в Repeater."""
        row = item.row()
        id_item = self.item(row, 0)
        
        if id_item:
            msg_id = int(id_item.text())
            msg = self._messages.get(msg_id)
            
            if msg:
                self.open_in_repeater.emit(msg)
    
    def clear_history(self):
        """Очищает таблицу."""
        self.setRowCount(0)
        self._messages.clear()
    
    def get_selected_message(self) -> HttpMessage | None:
        """Возвращает выбранное сообщение."""
        current_row = self.currentRow()
        if current_row >= 0:
            id_item = self.item(current_row, 0)
            if id_item:
                msg_id = int(id_item.text())
                return self._messages.get(msg_id)
        return None