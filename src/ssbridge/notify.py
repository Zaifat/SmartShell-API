"""Уведомления в Telegram (о сбоях и, по желанию, о переключениях)."""
from __future__ import annotations

import queue
import threading
import time

from . import journal
from .net import session

API = "https://api.telegram.org/bot{token}/sendMessage"


class Notifier:
    def __init__(self, get_settings):
        self._get = get_settings
        self._q: queue.Queue = queue.Queue(maxsize=100)
        self._http = session()
        self._last: dict[str, float] = {}
        threading.Thread(target=self._worker, name="notify", daemon=True).start()

    def _settings(self) -> dict:
        try:
            return self._get() or {}
        except Exception:
            return {}

    def enabled(self) -> bool:
        s = self._settings()
        return bool(s.get("telegram_token") and s.get("telegram_chat_id"))

    def error(self, text: str, key: str | None = None) -> None:
        if self._settings().get("on_errors", True):
            self.send("⚠️ " + text, key)

    def recovered(self, text: str) -> None:
        if self._settings().get("on_errors", True):
            self.send("✅ " + text)

    def switched(self, text: str) -> None:
        if self._settings().get("on_switch"):
            self.send("🔌 " + text)

    def send(self, text: str, key: str | None = None) -> None:
        if not self.enabled():
            return
        if key:  # не чаще раза в 10 минут для одной и той же проблемы
            now = time.time()
            if now - self._last.get(key, 0) < 600:
                return
            self._last[key] = now
        try:
            self._q.put_nowait(text)
        except queue.Full:
            pass

    def send_now(self, text: str) -> None:
        s = self._settings()
        if not (s.get("telegram_token") and s.get("telegram_chat_id")):
            raise ValueError("Укажите токен бота и chat id")
        r = self._http.post(API.format(token=s["telegram_token"].strip()),
                            json={"chat_id": str(s["telegram_chat_id"]).strip(), "text": text}, timeout=(5, 10))
        data = r.json()
        if not data.get("ok"):
            raise ValueError(data.get("description") or "ошибка Telegram")

    def _worker(self) -> None:
        while True:
            text = self._q.get()
            for attempt in range(3):
                try:
                    self.send_now("SmartShell Bridge: " + text)
                    break
                except Exception as e:
                    if attempt == 2:
                        journal.debug(f"Telegram: не удалось отправить уведомление: {e}", "notify")
                    time.sleep(5 * (attempt + 1))
