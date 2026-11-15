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
from .net import BridgeError

CONFIG_VERSION = 3
SECRET_KEYS = {"password", "token", "access_secret", "secret", "api_key", "lan_pin", "telegram_token"}
MASK = "••••••••"

DEFAULTS: dict[str, Any] = {
    "version": CONFIG_VERSION,
    # клубы (аккаунты) SmartShell: [{id, name, login, password, company_id, user_agent, enabled}]
    "clubs": [],
    "general": {
        "poll_interval": 10,
        "enforce_state": True,
        "dry_run": False,
        "autostart": False,  # включается только по выбору пользователя
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
                    if self._migrate():
                        try:
                            self.save()
                        except OSError:
                            pass
                    self.revision += 1
                    return
                except Exception as e:  # повреждённый файл
                    self.load_error = f"Не удалось прочитать {candidate.name}: {e}"
            self._data = copy.deepcopy(DEFAULTS)

    def _migrate(self) -> bool:
        """Перенос настроек старых версий. Возвращает True, если что-то изменилось."""
        d = self._data
        changed = False
        old = d.pop("smartshell", None)
        if isinstance(old, dict):
            changed = True
            if old.get("login") and not d.get("clubs"):
                cid = str(old.get("company_id", "")).strip()
                # старый интерфейс сохранял «Название — адрес»; оставляем только название
                name = str(old.get("club_name") or "").split(" — ")[0].strip()
                d["clubs"] = [{
                    "id": new_id("k"), "name": name or f"Клуб {cid}".strip(),
                    "login": old.get("login", ""), "password": old.get("password", ""),
                    "company_id": cid, "user_agent": old.get("user_agent", ""), "enabled": True,
                }]
        clubs = d.get("clubs") or []
        if clubs:
            first = clubs[0]["id"]
            for item in list(d.get("bindings") or []) + list(d.get("virtual_hosts") or []):
                if not item.get("club_id"):
                    item["club_id"] = first
                    changed = True
        if d.get("version") != CONFIG_VERSION:
            d["version"] = CONFIG_VERSION
            changed = True
        return changed

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

    # ---- клубы SmartShell ----
    CLUB_FIELDS = ("name", "login", "password", "company_id", "user_agent", "enabled")

    def clubs(self) -> list[dict]:
        return self.get("clubs") or []

    def club(self, kid: str) -> dict | None:
        return next((c for c in self.clubs() if c.get("id") == kid), None)

    def upsert_club(self, club: dict) -> dict:
        with self._lock:
            items = self._data.setdefault("clubs", [])
            data = {k: club[k] for k in self.CLUB_FIELDS if k in club}
            old = next((c for c in items if c["id"] == club.get("id")), None) if club.get("id") else None
            if club.get("id") and old is None:
                raise BridgeError("клуб не найден")
            merged = dict(old or {"id": new_id("k"), "name": "", "login": "", "password": "", "company_id": "",
                                  "user_agent": "", "enabled": True})
            merged.update(unmask_tree(data, old or {}))
            merged["company_id"] = str(merged.get("company_id") or "").strip()
            merged["login"] = str(merged.get("login") or "").strip()
            merged["name"] = str(merged.get("name") or "").strip() or f"Клуб {merged['company_id']}".strip()
            merged["enabled"] = bool(merged.get("enabled", True))
            if not merged["login"] or not merged["password"]:
                raise BridgeError("укажите логин и пароль SmartShell")
            if not merged["company_id"]:
                raise BridgeError("выберите клуб")
            dup = next((c for c in items if c["id"] != merged["id"] and c.get("company_id") == merged["company_id"]), None)
            if dup:
                raise BridgeError(f"клуб «{dup.get('name')}» уже добавлен")
            if old is not None:
                items[items.index(old)] = merged
            else:
                items.append(merged)
                # первый клуб: привязки без клуба (из старых версий) относятся к нему
                if len(items) == 1:
                    for x in list(self._data.get("bindings") or []) + list(self._data.get("virtual_hosts") or []):
                        if not x.get("club_id"):
                            x["club_id"] = merged["id"]
            self.save()
            return copy.deepcopy(merged)

    def delete_club(self, kid: str) -> None:
        with self._lock:
            before = len(self._data.get("clubs", []))
            self._data["clubs"] = [c for c in self._data.get("clubs", []) if c.get("id") != kid]
            if len(self._data["clubs"]) == before:
                raise BridgeError("клуб не найден")
            self._data["bindings"] = [b for b in self._data.get("bindings", []) if b.get("club_id") != kid]
            self._data["virtual_hosts"] = [v for v in self._data.get("virtual_hosts", []) if v.get("club_id") != kid]
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

    BINDING_FIELDS = ("enabled", "off_delay", "invert", "on_in_service")

    def add_binding(self, b: dict) -> tuple[dict, bool]:
        """Добавить привязку. Возвращает (привязка, создана_ли). Дубликаты не создаются."""
        with self._lock:
            items = self._data.setdefault("bindings", [])
            for x in items:
                if (str(x.get("host_id")) == str(b.get("host_id")) and x.get("connector_id") == b.get("connector_id")
                        and x.get("device_id") == b.get("device_id") and x.get("club_id", "") == (b.get("club_id") or "")):
                    return copy.deepcopy(x), False
            nb = {
                "id": new_id("b"), "club_id": b.get("club_id") or "", "host_id": b.get("host_id"), "host_alias": b.get("host_alias", ""),
                "connector_id": b["connector_id"], "device_id": b["device_id"], "device_name": b.get("device_name", ""),
                "enabled": bool(b.get("enabled", True)), "off_delay": max(0, int(b.get("off_delay") or 0)),
                "invert": bool(b.get("invert")), "on_in_service": bool(b.get("on_in_service")),
            }
            items.append(nb)
            self.save()
            return copy.deepcopy(nb), True

    def update_binding(self, bid: str, changes: dict) -> dict:
        with self._lock:
            for x in self._data.get("bindings", []):
                if x.get("id") == bid:
                    for k in self.BINDING_FIELDS:
                        if k in changes:
                            x[k] = max(0, min(86400, int(changes[k] or 0))) if k == "off_delay" else bool(changes[k])
                    self.save()
                    return copy.deepcopy(x)
        raise BridgeError("привязка не найдена")

    def delete_binding(self, bid: str) -> None:
        with self._lock:
            before = len(self._data.get("bindings", []))
            self._data["bindings"] = [x for x in self._data.get("bindings", []) if x.get("id") != bid]
            if len(self._data["bindings"]) == before:
                raise BridgeError("привязка не найдена")
            self.save()

    # ---- виртуальные хосты ----
    def virtual_hosts(self) -> list[dict]:
        return self.get("virtual_hosts") or []

    def add_virtual_host(self, host_id: int, alias: str, token: str, club_id: str = "") -> None:
        with self._lock:
            items = [v for v in self._data.get("virtual_hosts", [])
                     if not (v.get("host_id") == host_id and v.get("club_id", "") == club_id)]
            items.append({"club_id": club_id, "host_id": host_id, "alias": alias, "token": token})
            self._data["virtual_hosts"] = items
            self.save()

    def remove_virtual_host(self, host_id: int, club_id: str | None = None) -> None:
        with self._lock:
            self._data["virtual_hosts"] = [
                v for v in self._data.get("virtual_hosts", [])
                if not (v.get("host_id") == host_id and (club_id is None or v.get("club_id", "") == club_id))]
            self.save()
