"""Модели данных для HTTP-сообщений."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json


class MessageState(Enum):
    """Состояния обработки запроса."""
    RECEIVED = "Received"        # Получен от клиента, ждёт решения
    FORWARDED = "Forwarded"      # Отправлен на сервер
    DROPPED = "Dropped"          # Сброшен пользователем
    RESPONDED = "Responded"      # Получен ответ от сервера
    MODIFIED = "Modified"        # Изменён пользователем перед отправкой


@dataclass
class HttpMessage:
    """Полное HTTP-сообщение (запрос + ответ)."""
    
    id: int
    timestamp: datetime = field(default_factory=datetime.now)
    client_address: str = ""
    
    # Данные запроса
    method: str = "GET"
    url: str = ""
    host: str = ""
    port: int = 80
    path: str = "/"
    scheme: str = "http"
    request_headers: dict = field(default_factory=dict)
    request_body: Optional[bytes] = None
    
    # Данные ответа
    status_code: Optional[int] = None
    reason_phrase: Optional[str] = None
    response_headers: dict = field(default_factory=dict)
    response_body: Optional[bytes] = None
    
    # Метаданные
    state: MessageState = MessageState.RECEIVED
    comment: str = ""
    highlighted: bool = False
    
    # Время ответа в миллисекундах
    response_time_ms: Optional[int] = None
    
    @property
    def is_https(self) -> bool:
        return self.scheme == "https" or self.port == 443
    
    @property
    def response_length(self) -> int:
        if self.response_body:
            return len(self.response_body)
        return 0
    
    @property
    def request_length(self) -> int:
        length = 0
        if self.request_body:
            length += len(self.request_body)
        return length
    
    @property
    def content_type(self) -> str:
        """Определяет Content-Type ответа."""
        content_type = self.response_headers.get("Content-Type", "")
        if not content_type:
            content_type = self.response_headers.get("content-type", "")
        return content_type.lower()
    
    def get_header(self, name: str, from_request: bool = True) -> Optional[str]:
        """Получить заголовок без учёта регистра."""
        headers = self.request_headers if from_request else self.response_headers
        
        name_lower = name.lower()
        for key, value in headers.items():
            if key.lower() == name_lower:
                return value
        return None
    
    def set_header(self, name: str, value: str, for_request: bool = True):
        """Установить заголовок."""
        if for_request:
            self.request_headers[name] = value
        else:
            self.response_headers[name] = value
    
    def remove_header(self, name: str, from_request: bool = True):
        """Удалить заголовок."""
        headers = self.request_headers if from_request else self.response_headers
        headers.pop(name, None)
    
    def get_request_body_as_text(self) -> str:
        """Тело запроса как строка."""
        if self.request_body:
            return self.request_body.decode("utf-8", errors="replace")
        return ""
    
    def get_response_body_as_text(self) -> str:
        """Тело ответа как строка."""
        if self.response_body:
            return self.response_body.decode("utf-8", errors="replace")
        return ""
    
    def try_format_json(self, text: str) -> str:
        """Пытается отформатировать JSON."""
        try:
            data = json.loads(text)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            return text
    
    def to_dict(self) -> dict:
        """Сериализация для сохранения в файл."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "method": self.method,
            "url": self.url,
            "host": self.host,
            "path": self.path,
            "status_code": self.status_code,
            "request_headers": self.request_headers,
            "response_headers": self.response_headers,
            "response_time_ms": self.response_time_ms,
        }
    
    def __repr__(self):
        return f"HttpMessage(#{self.id} {self.method} {self.url} [{self.state.value}])"