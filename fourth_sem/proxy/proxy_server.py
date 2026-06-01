"""Запуск mitmproxy в отдельном потоке."""

import sys
import os
import threading
import asyncio
import time
from typing import Optional
from pathlib import Path

from mitmproxy.options import Options
from mitmproxy.master import Master
from mitmproxy.addons import default_addons

from .interceptor import Interceptor
from .cert_manager import CertManager


class ProxyServer:
    """Управляет жизненным циклом прокси-сервера."""
    
    def __init__(self, port: int = 8080, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        
        self.interceptor = Interceptor()
        self.cert_manager = CertManager()
        
        self._master: Optional[Master] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._ready = threading.Event()
        self._loop = None
    
    def start(self) -> None:
        """Запускает прокси-сервер в отдельном потоке."""
        
        if self._running:
            print("[ProxyServer] Already running")
            return
        
        print(f"[ProxyServer] Starting on {self.host}:{self.port}...")
        
        self._ready.clear()
        self._thread = threading.Thread(
            target=self._run_proxy,
            daemon=True,
            name="mitmproxy-thread"
        )
        self._thread.start()
        
        # Ждём готовности
        if not self._ready.wait(timeout=5.0):
            raise RuntimeError("Proxy failed to start within 5 seconds")
        
        self._running = True
        print(f"[ProxyServer] ✅ Running on {self.proxy_url}")
    
    def _run_proxy(self) -> None:
        """Запускает mitmproxy с собственным event loop."""
        
        try:
            # Создаём новый event loop для этого потока
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            # Настройки mitmproxy
            opts = Options()
            opts.listen_host = self.host
            opts.listen_port = self.port
            opts.ssl_insecure = True
            
            # Создаём Master
            self._master = Master(opts, self._loop)
            
            # Добавляем стандартные аддоны
            self._master.addons.add(*default_addons())
            
            # Добавляем наш перехватчик
            self._master.addons.add(self.interceptor)
            
            # Сигнализируем о готовности
            self._ready.set()
            
            # Запускаем event loop с master
            self._loop.run_until_complete(self._master.run())
            
        except Exception as e:
            print(f"[ProxyServer] Error: {e}")
            import traceback
            traceback.print_exc()
            self._ready.set()  # Чтобы не зависнуть
        finally:
            self._running = False
            if self._loop and not self._loop.is_closed():
                self._loop.close()
    
    def stop(self) -> None:
        """Останавливает прокси-сервер."""
        if not self._running and self._master is None:
            return
        
        print("[ProxyServer] Stopping...")
        self._running = False
        
        if self._master:
            self._master.shutdown()
        
        self.interceptor.shutdown()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        
        print("[ProxyServer] Stopped")
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def proxy_url(self) -> str:
        return f"{self.host}:{self.port}"
    
    def toggle_intercept(self) -> bool:
        """Переключает режим перехвата."""
        return self.interceptor.toggle_intercept()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()