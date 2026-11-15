"""Хранение настроек.

* JSON в папке данных, запись атомарная (через временный файл);
* перед каждой записью предыдущая версия сохраняется в ``config.bak.json``;
* если основной файл повреждён — автоматически берётся резервная копия;
* все поля с «секретными» именами (password, token, secret...) шифруются DPAPI.
"""
from __future__ import annotations

import copy
import json
import os
import threading
import uuid
from pathlib import Path
from typing import Any

from . import paths, secrets

CONFIG_VERSION = 2
SECRET_KEYS = {"password", "token", "access_secret", "secret", "api_key", "lan_pin", "telegram_token"}
MASK = "••••••••"

DEFAULTS: dict[str, Any] = {
    "version": CONFIG_VERSION,
    "smartshell": {
        "login": "",
        "password": "",
        "company_id": "",
        "club_name": "",
        "user_agent": "",
    },
    "general": {
        "poll_interval": 10,
        "enforce_state": True,
        "dry_run": False,
        "autostart": True,
        "start_minimized": True,
        "web_port": 8765,
        "allow_lan": False,
        "lan_pin": "",
        "keepalive_interval": 30,
        "max_billing_rpm": 15,
    },
    "notify": {
        "telegram_token": "",
        "telegram_chat_id": "",
        "on_errors": True,
        "on_switch": False,
    },
    "connectors": [],
    "bindings": [],
    "virtual_hosts": [],
    "wizard_done": False,
}


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _merge(defaults: Any, data: Any) -> Any:
    if isinstance(defaults, dict) and isinstance(data, dict):
        out = copy.deepcopy(defaults)
        for k, v in data.items():
            out[k] = _merge(defaults.get(k), v) if k in defaults else v
        return out
    return copy.deepcopy(data) if data is not None else copy.deepcopy(defaults)


def _walk_secrets(obj: Any, fn) -> Any:
    if isinstance(obj, dict):
        return {k: (fn(v) if k in SECRET_KEYS and isinstance(v, str) else _walk_secrets(v, fn)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_secrets(v, fn) for v in obj]
    return obj


def encrypt_tree(obj: Any) -> Any:
    return _walk_secrets(obj, lambda v: v if secrets.is_encrypted(v) else secrets.encrypt(v))


def decrypt_tree(obj: Any) -> Any:
    return _walk_secrets(obj, secrets.decrypt)


def mask_tree(obj: Any) -> Any:
    return _walk_secrets(obj, lambda v: MASK if v else "")


def unmask_tree(new: Any, old: Any) -> Any:
    """Заменить маску ``••••`` на прежнее значение секрета."""
    if isinstance(new, dict):
        old = old if isinstance(old, dict) else {}
        out = {}
        for k, v in new.items():
            if k in SECRET_KEYS and v == MASK:
                out[k] = old.get(k, "")
            else:
                out[k] = unmask_tree(v, old.get(k))
        return out
    if isinstance(new, list):
        old = old if isinstance(old, list) else []
        # элементы списков сопоставляем по id, если он есть
        by_id = {o.get("id"): o for o in old if isinstance(o, dict) and o.get("id")}
        res = []
        for i, v in enumerate(new):
            ref = by_id.get(v.get("id")) if isinstance(v, dict) and v.get("id") else (old[i] if i < len(old) else None)
            res.append(unmask_tree(v, ref))
        return res
    return new


class Config:
    """Потокобезопасный контейнер настроек (в памяти — расшифрованные)."""

    def __init__(self, path: Path | None = None):
        self.path = path or paths.config_path()
        self._lock = threading.RLock()
        self._data: dict[str, Any] = copy.deepcopy(DEFAULTS)
        self.revision = 0
        self.load_error: str | None = None
        self.load()

    # ---- чтение / запись ----
    def load(self) -> None:
        with self._lock:
            for candidate in (self.path, self._backup_path()):
                if not candidate.exists():
                    continue
                try:
                    raw = json.loads(candidate.read_text(encoding="utf-8"))
                    self._data = _merge(DEFAULTS, decrypt_tree(raw))
                    if candidate != self.path:
                        self.load_error = "Основной файл настроек повреждён, загружена резервная копия"
                    self.revision += 1
                    return
                except Exception as e:  # повреждённый файл
                    self.load_error = f"Не удалось прочитать {candidate.name}: {e}"
            self._data = copy.deepcopy(DEFAULTS)

    def _backup_path(self) -> Path:
        return self.path.with_name("config.bak.json")

    def save(self) -> None:
        with self._lock:
            payload = json.dumps(encrypt_tree(self._data), ensure_ascii=False, indent=2)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists():
                try:
                    self._backup_path().write_bytes(self.path.read_bytes())
                except OSError:
                    pass
            tmp = self.path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.path)
            self.revision += 1

    # ---- доступ ----
    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._data)

    def get(self, section: str, key: str | None = None, default: Any = None) -> Any:
        with self._lock:
            sec = self._data.get(section, default)
            if key is None:
                return copy.deepcopy(sec)
            if isinstance(sec, dict):
                return copy.deepcopy(sec.get(key, default))
            return default

    def update(self, section: str, value: Any, save: bool = True) -> None:
        with self._lock:
            if isinstance(value, dict) and isinstance(self._data.get(section), dict):
                merged = dict(self._data[section])
                merged.update(value)
                self._data[section] = merged
            else:
                self._data[section] = copy.deepcopy(value)
            if save:
                self.save()

    # ---- коннекторы ----
    def connectors(self) -> list[dict]:
        return self.get("connectors") or []

    def connector(self, cid: str) -> dict | None:
        return next((c for c in self.connectors() if c.get("id") == cid), None)

    def upsert_connector(self, conn: dict) -> dict:
        with self._lock:
            items = self._data.setdefault("connectors", [])
            if not conn.get("id"):
                conn["id"] = new_id("c")
            old = next((c for c in items if c["id"] == conn["id"]), None)
            if old is not None:
                conn = unmask_tree(conn, old)
                items[items.index(old)] = conn
            else:
                conn = unmask_tree(conn, {})
                items.append(conn)
            self.save()
            return copy.deepcopy(conn)

    def delete_connector(self, cid: str) -> None:
        with self._lock:
            self._data["connectors"] = [c for c in self._data.get("connectors", []) if c.get("id") != cid]
            self._data["bindings"] = [b for b in self._data.get("bindings", []) if b.get("connector_id") != cid]
            self.save()

    # ---- привязки ----
    def bindings(self) -> list[dict]:
        return self.get("bindings") or []

    def set_bindings(self, items: list[dict]) -> None:
        for b in items:
            b.setdefault("id", new_id("b"))
        self.update("bindings", items)

    # ---- виртуальные хосты ----
    def virtual_hosts(self) -> list[dict]:
        return self.get("virtual_hosts") or []

    def add_virtual_host(self, host_id: int, alias: str, token: str) -> None:
        with self._lock:
            items = [v for v in self._data.get("virtual_hosts", []) if v.get("host_id") != host_id]
            items.append({"host_id": host_id, "alias": alias, "token": token})
            self._data["virtual_hosts"] = items
            self.save()

    def remove_virtual_host(self, host_id: int) -> None:
        with self._lock:
            self._data["virtual_hosts"] = [v for v in self._data.get("virtual_hosts", []) if v.get("host_id") != host_id]
            self.save()
