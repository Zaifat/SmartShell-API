"""Пароль на вход в панель управления.

* пароль хранится только в виде хеша PBKDF2-SHA256 (200 000 итераций, соль);
* сессии — случайные токены в памяти программы (после перезапуска нужно войти снова);
* защита от подбора: после 5 неверных попыток с одного адреса — пауза 60 с.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time

ITERATIONS = 200_000
MIN_LENGTH = 4
SESSION_IDLE = 12 * 3600  # сессия истекает после 12 ч без активности
MAX_FAILS = 5
LOCK_SECONDS = 60


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt, digest = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iters))
        return hmac.compare_digest(dk.hex(), digest)
    except (ValueError, AttributeError):
        return False


def check_new_password(password: str) -> None:
    from .net import BridgeError
    if len(password or "") < MIN_LENGTH:
        raise BridgeError(f"пароль должен быть не короче {MIN_LENGTH} символов")


class Sessions:
    def __init__(self):
        self._lock = threading.Lock()
        self._tokens: dict[str, float] = {}
        self._fails: dict[str, list[float]] = {}

    def create(self) -> str:
        tok = secrets.token_urlsafe(32)
        with self._lock:
            self._tokens[tok] = time.time()
        return tok

    def valid(self, tok: str | None) -> bool:
        if not tok:
            return False
        now = time.time()
        with self._lock:
            for t, seen in list(self._tokens.items()):
                if now - seen > SESSION_IDLE:
                    self._tokens.pop(t, None)
            for t in self._tokens:
                if hmac.compare_digest(t, tok):
                    self._tokens[t] = now
                    return True
        return False

    def drop(self, tok: str | None) -> None:
        with self._lock:
            self._tokens.pop(tok or "", None)

    def clear(self) -> None:
        with self._lock:
            self._tokens.clear()

    # ---- защита от подбора
    def locked_for(self, addr: str) -> int:
        """Сколько секунд ещё заблокирован вход с адреса (0 — не заблокирован)."""
        now = time.time()
        with self._lock:
            fails = [t for t in self._fails.get(addr, []) if now - t < LOCK_SECONDS]
            self._fails[addr] = fails
            if len(fails) >= MAX_FAILS:
                return max(1, int(LOCK_SECONDS - (now - fails[-MAX_FAILS])))
        return 0

    def failed(self, addr: str) -> None:
        with self._lock:
            self._fails.setdefault(addr, []).append(time.time())

    def succeeded(self, addr: str) -> None:
        with self._lock:
            self._fails.pop(addr, None)
