"""Базовый класс коннектора к системе умного дома.

Чтобы добавить новую систему, достаточно унаследоваться от ``Connector``,
описать поля настроек в ``fields`` и реализовать ``list_devices`` и
``set_state``, затем зарегистрировать класс декоратором ``@register``.
"""
from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, ClassVar

from ..net import BridgeError, session

REGISTRY: dict[str, type["Connector"]] = {}


def register(cls: type["Connector"]) -> type["Connector"]:
    REGISTRY[cls.type_id] = cls
    return cls


@dataclass
class Device:
    id: str
    name: str
    state: bool | None = None  # None — состояние неизвестно
    room: str = ""
    kind: str = ""
    online: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def field(key: str, label: str, type: str = "text", required: bool = False, default: Any = "",
          help: str = "", options: list | None = None, columns: list | None = None, placeholder: str = "") -> dict:
    """Описание поля настройки для автоматической генерации формы в UI.

    type: text | password | number | bool | select | table
    Для table — columns: список полей той же структуры (строки таблицы).
    """
    d = {"key": key, "label": label, "type": type, "required": required, "default": default, "help": help,
         "placeholder": placeholder}
    if options is not None:
        d["options"] = options
    if columns is not None:
        d["columns"] = columns
    return d


def col(key: str, label: str, type: str = "text", default: Any = "", placeholder: str = "", options: list | None = None,
        required: bool = False) -> dict:
    return field(key, label, type, required=required, default=default, placeholder=placeholder, options=options)


class Connector:
    type_id: ClassVar[str] = ""
    title: ClassVar[str] = ""
    description: ClassVar[str] = ""
    category: ClassVar[str] = "cloud"  # cloud | local | universal
    icon: ClassVar[str] = "plug"
    docs: ClassVar[str] = ""          # краткая инструкция (HTML)
    fields: ClassVar[list[dict]] = []
    # True — список устройств задаётся вручную в таблице ``devices``
    manual_devices: ClassVar[bool] = False

    def __init__(self, cid: str, name: str, settings: dict):
        self.id = cid
        self.name = name
        self.settings = dict(settings or {})
        self.http = session()
        self.lock = threading.RLock()
        self._cache: dict[str, Device] = {}
        self._cache_ts = 0.0

    # ---- helpers ----
    def opt(self, key: str, default: Any = "") -> Any:
        v = self.settings.get(key)
        if v is None or v == "":
            for f in self.fields:
                if f["key"] == key:
                    return f.get("default", default)
            return default
        return v

    def require(self, *keys: str) -> None:
        missing = [k for k in keys if not str(self.settings.get(k) or "").strip()]
        if missing:
            labels = {f["key"]: f["label"] for f in self.fields}
            raise BridgeError("не заполнено: " + ", ".join(labels.get(k, k) for k in missing))

    def rows(self) -> list[dict]:
        """Строки таблицы устройств (для коннекторов с ручным списком)."""
        return [r for r in (self.settings.get("devices") or []) if isinstance(r, dict) and any(str(v).strip() for v in r.values())]

    def row(self, device_id: str) -> dict:
        for i, r in enumerate(self.rows()):
            if self.row_id(r, i) == device_id:
                return r
        raise BridgeError(f"устройство {device_id} не найдено в списке")

    @staticmethod
    def row_id(r: dict, index: int) -> str:
        return str(r.get("name") or f"#{index + 1}").strip()

    # ---- API ----
    def test(self) -> str:
        """Проверка подключения. Возвращает сообщение или бросает BridgeError."""
        devs = self.list_devices()
        return f"Подключение успешно, найдено устройств: {len(devs)}"

    def list_devices(self) -> list[Device]:
        raise NotImplementedError

    def set_state(self, device_id: str, on: bool) -> None:
        raise NotImplementedError

    def get_states(self, device_ids: list[str]) -> dict[str, bool | None]:
        """Состояния нужных устройств. По умолчанию — из общего списка."""
        devs = {d.id: d for d in self.list_devices()}
        self._cache = devs
        self._cache_ts = time.time()
        return {i: (devs[i].state if i in devs else None) for i in device_ids}

    def close(self) -> None:
        try:
            self.http.close()
        except Exception:
            pass


def schema() -> list[dict]:
    order = ["yandex", "homeassistant", "tuya", "smartthings", "shelly", "tasmota", "sonoff", "mqtt",
             "openhab", "domoticz", "iobroker", "webhook"]
    out = []
    for cls in sorted(REGISTRY.values(), key=lambda c: order.index(c.type_id) if c.type_id in order else 99):
        out.append({
            "type": cls.type_id, "title": cls.title, "description": cls.description, "category": cls.category,
            "icon": cls.icon, "docs": cls.docs, "fields": cls.fields, "manual_devices": cls.manual_devices,
        })
    return out


def create(conf: dict) -> Connector:
    cls = REGISTRY.get(conf.get("type", ""))
    if not cls:
        raise BridgeError(f"неизвестный тип системы: {conf.get('type')}")
    return cls(conf.get("id", ""), conf.get("name") or cls.title, conf.get("settings") or {})


def as_bool(v: Any) -> bool | None:
    if isinstance(v, bool):
        return v
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in ("1", "on", "true", "yes", "вкл", "open", "opened", "playing", "home", "heat", "cool"):
        return True
    if s in ("0", "off", "false", "no", "выкл", "closed", "standby", "idle", "unavailable", "unknown", ""):
        return False if s not in ("unavailable", "unknown", "") else None
    try:
        return float(s) > 0
    except ValueError:
        return None
