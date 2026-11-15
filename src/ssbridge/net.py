"""Общие сетевые утилиты: HTTP-сессия, ошибки, ограничитель частоты."""
from __future__ import annotations

import collections
import threading
import time

import requests

from . import __version__

DEFAULT_TIMEOUT = (5, 15)  # подключение, чтение
USER_AGENT = f"SmartShellBridge/{__version__}"


class BridgeError(Exception):
    """Понятная пользователю ошибка (текст показывается в журнале и UI)."""


class AuthError(BridgeError):
    """Ошибка авторизации (неверный логин/токен)."""


def session(user_agent: str | None = None) -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = user_agent or USER_AGENT
    return s


def describe(exc: Exception) -> str:
    """Человекочитаемое описание сетевой ошибки."""
    if isinstance(exc, BridgeError):
        return str(exc)
    if isinstance(exc, requests.exceptions.ConnectTimeout):
        return "превышено время подключения (нет сети или устройство недоступно)"
    if isinstance(exc, requests.exceptions.ReadTimeout):
        return "сервер не ответил вовремя"
    if isinstance(exc, requests.exceptions.SSLError):
        return "ошибка SSL-сертификата"
    if isinstance(exc, requests.exceptions.ConnectionError):
        return "нет соединения (проверьте интернет / адрес устройства)"
    if isinstance(exc, requests.exceptions.HTTPError) and exc.response is not None:
        code = exc.response.status_code
        hint = {401: "неверный токен/пароль", 403: "доступ запрещён", 404: "не найдено", 429: "слишком много запросов"}.get(code, "")
        return f"HTTP {code}{(' — ' + hint) if hint else ''}"
    if isinstance(exc, ValueError):
        return f"некорректный ответ сервера ({exc})"
    return f"{type(exc).__name__}: {exc}"


def check_http(resp: requests.Response) -> requests.Response:
    if resp.status_code in (401, 403):
        raise AuthError(f"HTTP {resp.status_code}: неверный токен или нет доступа")
    resp.raise_for_status()
    return resp


class RateLimiter:
    """Скользящее окно: не более ``limit`` запросов за ``period`` секунд.

    SmartShell API: «не более 20 запросов в минуту по одному company_id».
    """

    def __init__(self, limit: int = 15, period: float = 60.0):
        self.limit = max(1, int(limit))
        self.period = period
        self._calls: collections.deque = collections.deque()
        self._lock = threading.Lock()

    def set_limit(self, limit: int) -> None:
        self.limit = max(1, int(limit))

    def _purge(self, now: float) -> None:
        while self._calls and now - self._calls[0] >= self.period:
            self._calls.popleft()

    def wait_time(self) -> float:
        with self._lock:
            now = time.monotonic()
            self._purge(now)
            if len(self._calls) < self.limit:
                return 0.0
            return self.period - (now - self._calls[0])

    def acquire(self, max_wait: float = 30.0) -> bool:
        deadline = time.monotonic() + max_wait
        while True:
            with self._lock:
                now = time.monotonic()
                self._purge(now)
                if len(self._calls) < self.limit:
                    self._calls.append(now)
                    return True
                wait = self.period - (now - self._calls[0])
            if now + wait > deadline:
                return False
            time.sleep(min(wait, 1.0) + 0.01)

    def used(self) -> int:
        with self._lock:
            self._purge(time.monotonic())
            return len(self._calls)
