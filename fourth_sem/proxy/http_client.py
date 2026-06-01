"""HTTP-клиент для Repeater'а (отправка отдельных запросов)."""

import requests
import time
import urllib3
from typing import Optional

# Отключаем предупреждения для самоподписанных сертификатов
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HttpClient:
    """HTTP-клиент для повторной отправки запросов.
    
    Использует библиотеку requests, 
    игнорирует проверку SSL (так как мы MITM).
    """
    
    def __init__(self, timeout: int = 30, verify_ssl: bool = False):
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        
        # Отключаем SSL предупреждения
        if not verify_ssl:
            self.session.verify = False
    
    def send(self, 
             method: str,
             url: str,
             headers: Optional[dict] = None,
             body: Optional[bytes] = None) -> dict:
        """Отправляет HTTP-запрос и возвращает ответ.
        
        Returns:
            dict с ключами:
                - status_code: int
                - reason: str
                - headers: dict
                - body: bytes
                - elapsed_ms: int
                - error: str или None
        """
        
        if headers is None:
            headers = {}
        
        # Убираем заголовки, которые requests добавит сам
        headers.pop("Content-Length", None)
        headers.pop("Host", None)
        headers.pop("Connection", None)
        
        result = {
            "status_code": 0,
            "reason": "",
            "headers": {},
            "body": b"",
            "elapsed_ms": 0,
            "error": None,
        }
        
        try:
            start_time = time.time()
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                timeout=self.timeout,
                allow_redirects=True,
                verify=self.verify_ssl,
            )
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            result["status_code"] = response.status_code
            result["reason"] = response.reason
            result["headers"] = dict(response.headers)
            result["body"] = response.content
            result["elapsed_ms"] = elapsed_ms
            
        except requests.exceptions.SSLError as e:
            result["error"] = f"SSL Error: {e}"
        except requests.exceptions.ConnectTimeout:
            result["error"] = "Connection timeout"
        except requests.exceptions.ReadTimeout:
            result["error"] = "Read timeout"
        except requests.exceptions.ConnectionError as e:
            result["error"] = f"Connection error: {e}"
        except Exception as e:
            result["error"] = f"Error: {e}"
        
        return result
    
    def send_raw(self, raw_request: str) -> dict:
        """Отправляет сырой HTTP-запрос (как текст).
        
        Парсит первую строку как 'METHOD /path HTTP/1.1',
        извлекает заголовки и тело.
        """
        
        lines = raw_request.strip().split("\n")
        
        if not lines:
            return {"error": "Empty request"}
        
        # Парсим request line
        request_line = lines[0].strip().split(" ")
        if len(request_line) < 2:
            return {"error": "Invalid request line"}
        
        method = request_line[0]
        path = request_line[1]
        
        # Парсим заголовки и тело
        headers = {}
        body = None
        body_start = -1
        
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if line == "":
                body_start = i + 1
                break
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        
        if body_start > 0 and body_start < len(lines):
            body = "\n".join(lines[body_start:]).encode("utf-8")
        
        # Определяем URL
        host = headers.get("Host", "localhost")
        scheme = "https" if ":443" in host else "http"
        url = f"{scheme}://{host}{path}"
        
        return self.send(method, url, headers, body)
    
    def close(self):
        """Закрывает сессию."""
        self.session.close()