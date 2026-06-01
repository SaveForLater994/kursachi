"""Перехватчик HTTP/HTTPS трафика."""

from mitmproxy import http, ctx
from typing import Optional, Callable
import threading
import queue

from .models import HttpMessage, MessageState


class Interceptor:
    """Основной перехватчик mitmproxy."""
    
    def __init__(self):
        self._queue: queue.Queue[HttpMessage] = queue.Queue()
        self._pending_events: dict[int, threading.Event] = {}
        self._pending_decisions: dict[int, str] = {}
        self._counter = 0
        self._lock = threading.Lock()
        
        self.intercept_enabled = False
        
        self.on_request_captured: Optional[Callable[[HttpMessage], None]] = None
        self.on_response_received: Optional[Callable[[HttpMessage], None]] = None
        
        self.history: dict[int, HttpMessage] = {}
    
    def request(self, flow: http.HTTPFlow) -> None:
        """Вызывается mitmproxy при получении запроса."""
        
        with self._lock:
            self._counter += 1
            msg_id = self._counter
        
        # Создаём модель
        msg = HttpMessage(
            id=msg_id,
            client_address=f"{flow.client_conn.address[0]}:{flow.client_conn.address[1]}",
            method=flow.request.method,
            url=flow.request.pretty_url,
            host=flow.request.pretty_host,
            port=flow.request.port,
            path=flow.request.path,
            scheme=flow.request.scheme,
            request_headers=dict(flow.request.headers),
            request_body=flow.request.content if flow.request.content else None,
            state=MessageState.RECEIVED,
        )
        
        self.history[msg_id] = msg
        flow.msg_id = msg_id
        
        if self.on_request_captured:
            self.on_request_captured(msg)
        
        if self.intercept_enabled:
            self._queue.put(msg)
            
            event = threading.Event()
            self._pending_events[msg_id] = event
            
            # Ждём решения пользователя
            event.wait()
            
            decision = self._pending_decisions.pop(msg_id, "forward")
            self._pending_events.pop(msg_id, None)
            
            if decision == "drop":
                flow.kill()
                msg.state = MessageState.DROPPED
            elif decision == "forward":
                msg.state = MessageState.FORWARDED
                if msg.state == MessageState.MODIFIED:
                    self._apply_modifications(flow, msg)
        else:
            msg.state = MessageState.FORWARDED
    
    def response(self, flow: http.HTTPFlow) -> None:
        """Вызывается mitmproxy при получении ответа."""
        
        msg_id = getattr(flow, "msg_id", None)
        if msg_id is None:
            return
        
        msg = self.history.get(msg_id)
        if msg is None:
            return
        
        msg.status_code = flow.response.status_code
        msg.reason_phrase = flow.response.reason
        msg.response_headers = dict(flow.response.headers)
        msg.response_body = flow.response.content if flow.response.content else None
        
        if msg.state == MessageState.FORWARDED:
            msg.state = MessageState.RESPONDED
        
        if self.on_response_received:
            self.on_response_received(msg)
    
    def _apply_modifications(self, flow: http.HTTPFlow, msg: HttpMessage) -> None:
        """Применяет модификации к flow."""
        if msg.method != flow.request.method:
            flow.request.method = msg.method
        if msg.path != flow.request.path:
            flow.request.path = msg.path
        for key, value in msg.request_headers.items():
            flow.request.headers[key] = value
        if msg.request_body is not None:
            flow.request.content = msg.request_body
    
    def wait_for_intercepted(self, timeout: Optional[float] = None) -> Optional[HttpMessage]:
        """Блокирующий вызов: ждёт следующий перехваченный запрос."""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def poll_intercepted(self) -> Optional[HttpMessage]:
        """Неблокирующая проверка очереди перехваченных запросов."""
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None
    
    def forward(self, msg_id: int) -> bool:
        """Разрешить запрос."""
        event = self._pending_events.get(msg_id)
        if event:
            self._pending_decisions[msg_id] = "forward"
            event.set()
            return True
        return False
    
    def drop(self, msg_id: int) -> bool:
        """Сбросить запрос."""
        event = self._pending_events.get(msg_id)
        if event:
            self._pending_decisions[msg_id] = "drop"
            event.set()
            return True
        return False
    
    def modify_and_forward(self, msg_id: int, modified_msg: HttpMessage) -> bool:
        """Изменить и отправить."""
        event = self._pending_events.get(msg_id)
        if event:
            original = self.history.get(msg_id)
            if original:
                original.method = modified_msg.method
                original.path = modified_msg.path
                original.request_headers = modified_msg.request_headers
                original.request_body = modified_msg.request_body
                original.state = MessageState.MODIFIED
            
            self._pending_decisions[msg_id] = "forward"
            event.set()
            return True
        return False
    
    def toggle_intercept(self) -> bool:
        """Переключает режим перехвата."""
        self.intercept_enabled = not self.intercept_enabled
        return self.intercept_enabled
    
    def get_history(self) -> list[HttpMessage]:
        """Возвращает историю."""
        return sorted(self.history.values(), key=lambda m: m.id, reverse=True)
    
    def get_message(self, msg_id: int) -> Optional[HttpMessage]:
        """Получить сообщение по ID."""
        return self.history.get(msg_id)
    
    def clear_history(self) -> None:
        """Очищает историю."""
        self.history.clear()
    
    def shutdown(self) -> None:
        """Завершает работу."""
        # Отпускаем все ожидающие запросы
        for event in self._pending_events.values():
            event.set()
        self._pending_events.clear()
        self._pending_decisions.clear()
        
        # Очищаем очередь
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break