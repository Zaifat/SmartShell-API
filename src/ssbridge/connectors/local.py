"""Локальные устройства в сети клуба (без облака): Shelly, Tasmota, Sonoff DIY."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from ..net import BridgeError, check_http
from .base import Connector, Device, as_bool, col, field, register


def _host(addr: str) -> str:
    addr = (addr or "").strip().rstrip("/")
    if not addr:
        raise BridgeError("не указан IP-адрес устройства")
    return addr if addr.startswith("http") else f"http://{addr}"


class _LocalBase(Connector):
    category = "local"
    manual_devices = True

    def _probe(self, row: dict) -> bool | None:
        raise NotImplementedError

    def list_devices(self) -> list[Device]:
        rows = self.rows()
        if not rows:
            return []

        def one(item):
            i, r = item
            try:
                return Device(id=self.row_id(r, i), name=self.row_id(r, i), state=self._probe(r), kind=self.type_id)
            except Exception:
                return Device(id=self.row_id(r, i), name=self.row_id(r, i), state=None, kind=self.type_id, online=False)

        with ThreadPoolExecutor(max_workers=min(8, len(rows))) as ex:
            return list(ex.map(one, enumerate(rows)))

    def get_states(self, device_ids: list[str]) -> dict[str, bool | None]:
        res = {}
        for did in device_ids:
            try:
                res[did] = self._probe(self.row(did))
            except Exception:
                res[did] = None
        return res

    def test(self) -> str:
        devs = self.list_devices()
        if not devs:
            raise BridgeError("добавьте хотя бы одно устройство в таблицу")
        bad = [d.name for d in devs if not d.online]
        if bad:
            raise BridgeError(f"нет ответа от: {', '.join(bad)}")
        return f"Все устройства отвечают ({len(devs)})"


DEV_COLS = [
    col("name", "Название", required=True, placeholder="PS5-1"),
    col("address", "IP-адрес", required=True, placeholder="192.168.1.50"),
    col("channel", "Канал", "number", default=0),
]


@register
class Shelly(_LocalBase):
    type_id = "shelly"
    title = "Shelly"
    description = "Реле и розетки Shelly (Gen1, Plus/Pro, Gen3/Gen4) по локальной сети"
    icon = "shelly"
    docs = "Укажите IP-адреса устройств (их видно в приложении Shelly или в роутере). Канал 0 — первое реле. Поколение определяется автоматически."
    fields = [
        field("username", "Логин (если включена защита)", default="admin"),
        field("password", "Пароль (если включена защита)", "password"),
        field("devices", "Устройства", "table", columns=DEV_COLS),
    ]

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._gen: dict[str, int] = {}

    def _auth(self, gen: int):
        pw = self.settings.get("password")
        if not pw:
            return None
        user = self.opt("username", "admin")
        return HTTPDigestAuth(user, pw) if gen >= 2 else HTTPBasicAuth(user, pw)

    def _generation(self, base: str) -> int:
        if base not in self._gen:
            info = self.http.get(f"{base}/shelly", timeout=(3, 5)).json()
            self._gen[base] = int(info.get("gen") or 1)
        return self._gen[base]

    def _probe(self, row: dict) -> bool | None:
        base, ch = _host(row.get("address")), int(row.get("channel") or 0)
        gen = self._generation(base)
        if gen >= 2:
            r = check_http(self.http.get(f"{base}/rpc/Switch.GetStatus", params={"id": ch}, auth=self._auth(gen), timeout=(3, 5)))
            return as_bool(r.json().get("output"))
        r = check_http(self.http.get(f"{base}/relay/{ch}", auth=self._auth(gen), timeout=(3, 5)))
        return as_bool(r.json().get("ison"))

    def set_state(self, device_id: str, on: bool) -> None:
        row = self.row(device_id)
        base, ch = _host(row.get("address")), int(row.get("channel") or 0)
        gen = self._generation(base)
        if gen >= 2:
            check_http(self.http.get(f"{base}/rpc/Switch.Set", params={"id": ch, "on": "true" if on else "false"},
                                     auth=self._auth(gen), timeout=(3, 8)))
        else:
            check_http(self.http.get(f"{base}/relay/{ch}", params={"turn": "on" if on else "off"}, auth=self._auth(gen), timeout=(3, 8)))


@register
class Tasmota(_LocalBase):
    type_id = "tasmota"
    title = "Tasmota"
    description = "Розетки и реле с прошивкой Tasmota (Sonoff, Blitzwolf, Gosund и др.)"
    icon = "tasmota"
    docs = "Укажите IP-адрес устройства. Канал: 0 или 1 — первое реле, 2 — второе и т.д."
    fields = [
        field("username", "Логин веб-интерфейса", default="admin"),
        field("password", "Пароль веб-интерфейса", "password"),
        field("devices", "Устройства", "table", columns=DEV_COLS),
    ]

    def _cmd(self, row: dict, cmnd: str) -> dict:
        params = {"cmnd": cmnd}
        if self.settings.get("password"):
            params.update(user=self.opt("username", "admin"), password=self.settings["password"])
        return check_http(self.http.get(f"{_host(row.get('address'))}/cm", params=params, timeout=(3, 6))).json()

    @staticmethod
    def _power(row: dict) -> str:
        ch = int(row.get("channel") or 0)
        return "Power" if ch <= 1 else f"Power{ch}"

    def _probe(self, row: dict) -> bool | None:
        data = self._cmd(row, self._power(row))
        ch = int(row.get("channel") or 0)
        for key in ([f"POWER{ch}"] if ch > 1 else ["POWER", "POWER1"]):
            if key in data:
                return as_bool(data[key])
        if "WARNING" in data:
            raise BridgeError(f"Tasmota: {data['WARNING']}")
        return None

    def set_state(self, device_id: str, on: bool) -> None:
        data = self._cmd(self.row(device_id), f"{self._power(self.row(device_id))} {'On' if on else 'Off'}")
        if "WARNING" in data:
            raise BridgeError(f"Tasmota: {data['WARNING']}")


@register
class SonoffDIY(_LocalBase):
    type_id = "sonoff"
    title = "Sonoff (режим DIY / LAN)"
    description = "Устройства Sonoff/eWeLink в локальном режиме DIY без облака"
    icon = "sonoff"
    docs = "Включите на устройстве режим DIY (LAN) по инструкции Sonoff. API работает на порту 8081."
    fields = [field("devices", "Устройства", "table", columns=[
        col("name", "Название", required=True, placeholder="ТВ-1"),
        col("address", "IP-адрес", required=True, placeholder="192.168.1.60"),
        col("channel", "Канал (для многоканальных)", "number", default=0),
    ])]

    @staticmethod
    def _base(row: dict) -> str:
        b = _host(row.get("address"))
        return b if b.count(":") >= 2 else f"{b}:8081"

    def _probe(self, row: dict) -> bool | None:
        data = check_http(self.http.post(f"{self._base(row)}/zeroconf/info", json={"deviceid": "", "data": {}}, timeout=(3, 5))).json()
        d = data.get("data") or {}
        if "switches" in d:
            ch = int(row.get("channel") or 0)
            sw = next((s for s in d["switches"] if int(s.get("outlet", -1)) == ch), None)
            return as_bool(sw.get("switch")) if sw else None
        return as_bool(d.get("switch"))

    def set_state(self, device_id: str, on: bool) -> None:
        row = self.row(device_id)
        val = "on" if on else "off"
        info = check_http(self.http.post(f"{self._base(row)}/zeroconf/info", json={"deviceid": "", "data": {}}, timeout=(3, 5))).json()
        if "switches" in (info.get("data") or {}):
            payload, path = {"switches": [{"switch": val, "outlet": int(row.get("channel") or 0)}]}, "switches"
        else:
            payload, path = {"switch": val}, "switch"
        data = check_http(self.http.post(f"{self._base(row)}/zeroconf/{path}", json={"deviceid": "", "data": payload}, timeout=(3, 6))).json()
        if data.get("error") not in (0, None):
            raise BridgeError(f"Sonoff: ошибка {data.get('error')}")
