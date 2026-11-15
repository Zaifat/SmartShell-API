"""Журнал работы.

* файл ``logs/bridge.log`` с ротацией (5 файлов по 2 МБ);
* кольцевой буфер последних записей для веб-панели;
* подавление повторов: одинаковая ошибка пишется один раз, затем
  напоминание раз в 5 минут, а при восстановлении — запись «восстановлено».
"""
from __future__ import annotations

import collections
import logging
import threading
import time
from logging.handlers import RotatingFileHandler

from . import paths

log = logging.getLogger("ssbridge")

LEVELS = {"DEBUG": 10, "INFO": 20, "SUCCESS": 25, "WARNING": 30, "ERROR": 40}
logging.addLevelName(25, "SUCCESS")


class _RingHandler(logging.Handler):
    def __init__(self, capacity: int = 2000):
        super().__init__()
        self.items: collections.deque = collections.deque(maxlen=capacity)
        self.seq = 0
        self._ring_lock = threading.Lock()
        self.listeners: list = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = record.getMessage()
            if record.exc_info:
                msg += " | " + logging.Formatter().formatException(record.exc_info).splitlines()[-1]
            with self._ring_lock:
                self.seq += 1
                item = {
                    "id": self.seq,
                    "ts": record.created,
                    "level": record.levelname,
                    "cat": getattr(record, "cat", "system"),
                    "msg": msg,
                }
                self.items.append(item)
            for fn in list(self.listeners):
                try:
                    fn(item)
                except Exception:
                    pass
        except Exception:
            self.handleError(record)

    def since(self, after: int = 0, level: str | None = None, limit: int = 500) -> list[dict]:
        min_level = LEVELS.get((level or "DEBUG").upper(), 10)
        with self._ring_lock:
            rows = [i for i in self.items if i["id"] > after and LEVELS.get(i["level"], 20) >= min_level]
        return rows[-limit:]


ring = _RingHandler()
_configured = False


def setup(debug: bool = False, to_file: bool = True) -> None:
    global _configured
    if _configured:
        return
    _configured = True
    log.setLevel(logging.DEBUG)
    log.propagate = False
    ring.setLevel(logging.DEBUG)
    log.addHandler(ring)
    if to_file:
        fh = RotatingFileHandler(paths.logs_dir() / "bridge.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
        fh.setLevel(logging.DEBUG if debug else logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(cat)s] %(message)s", defaults={"cat": "system"}))
        log.addHandler(fh)


def write(level: str, msg: str, cat: str = "system", exc: bool = False) -> None:
    log.log(LEVELS.get(level, 20), msg, extra={"cat": cat}, exc_info=exc)


def debug(msg: str, cat: str = "system") -> None:
    write("DEBUG", msg, cat)


def info(msg: str, cat: str = "system") -> None:
    write("INFO", msg, cat)


def success(msg: str, cat: str = "system") -> None:
    write("SUCCESS", msg, cat)


def warning(msg: str, cat: str = "system") -> None:
    write("WARNING", msg, cat)


def error(msg: str, cat: str = "system", exc: bool = False) -> None:
    write("ERROR", msg, cat, exc)


class Problem:
    """Отслеживание повторяющейся проблемы (без спама в журнал)."""

    REMIND_EVERY = 300

    def __init__(self, key: str, cat: str = "system", on_change=None):
        self.key = key
        self.cat = cat
        self.active = False
        self.since = 0.0
        self.last_logged = 0.0
        self.last_message = ""
        self.count = 0
        self.on_change = on_change

    def fail(self, message: str, level: str = "ERROR") -> bool:
        """Отметить сбой. Возвращает True, если это новая проблема."""
        now = time.time()
        self.count += 1
        new = not self.active
        if new or message != self.last_message or now - self.last_logged > self.REMIND_EVERY:
            suffix = "" if new else f" (повторяется {self.count} раз, с {time.strftime('%H:%M:%S', time.localtime(self.since))})"
            write(level, message + suffix, self.cat)
            self.last_logged = now
        if new:
            self.active = True
            self.since = now
            if self.on_change:
                self.on_change(self.key, True, message)
        self.last_message = message
        return new

    def ok(self, message: str | None = None) -> bool:
        """Отметить восстановление. Возвращает True, если проблема была."""
        if not self.active:
            self.count = 0
            return False
        dur = int(time.time() - self.since)
        success((message or f"{self.key}: работа восстановлена") + f" (сбой длился {dur} с)", self.cat)
        self.active = False
        self.count = 0
        self.last_message = ""
        if self.on_change:
            self.on_change(self.key, False, message or "")
        return True
