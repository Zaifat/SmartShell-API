"""Локальные хабы и платформы: openHAB, Domoticz, ioBroker, а также универсальные HTTP-вебхуки."""
from __future__ import annotations

from requests.auth import HTTPBasicAuth

from ..net import BridgeError, check_http
from .base import Connector, Device, as_bool, col, field, register


@register
class OpenHAB(Connector):
    type_id = "openhab"
    title = "openHAB"
    description = "Элементы Switch в openHAB 3/4/5"
    category = "universal"
    icon = "openhab"
    docs = "Создайте API-токен: профиль пользователя openHAB → API Tokens. Используются элементы (Items) типа Switch."
    fields = [
        field("url", "Адрес openHAB", required=True, placeholder="http://192.168.1.20:8080"),
        field("token", "API-токен", "password"),
    ]

    def _base(self) -> str:
        self.require("url")
        return self.settings["url"].strip().rstrip("/")

    def _h(self) -> dict:
        tok = (self.settings.get("token") or "").strip()
        return {"Authorization": f"Bearer {tok}"} if tok else {}

    def list_devices(self) -> list[Device]:
        r = check_http(self.http.get(f"{self._base()}/rest/items", params={"type": "Switch", "recursive": "false"},
                                     headers=self._h(), timeout=(5, 15)))
        return [Device(id=i["name"], name=i.get("label") or i["name"], state=as_bool(i.get("state")), kind="Switch")
                for i in r.json()]

    def set_state(self, device_id: str, on: bool) -> None:
        h = dict(self._h(), **{"Content-Type": "text/plain"})
        check_http(self.http.post(f"{self._base()}/rest/items/{device_id}", data="ON" if on else "OFF", headers=h, timeout=(5, 10)))


@register
class Domoticz(Connector):
    type_id = "domoticz"
    title = "Domoticz"
    description = "Выключатели и розетки в Domoticz"
    category = "universal"
    icon = "domoticz"
    docs = "Укажите адрес Domoticz. Логин и пароль нужны, если включена авторизация."
    fields = [
        field("url", "Адрес Domoticz", required=True, placeholder="http://192.168.1.30:8080"),
        field("username", "Логин"),
        field("password", "Пароль", "password"),
    ]

    def _get(self, **params) -> dict:
        self.require("url")
        auth = HTTPBasicAuth(self.settings.get("username", ""), self.settings["password"]) if self.settings.get("password") else None
        r = check_http(self.http.get(f"{self.settings['url'].strip().rstrip('/')}/json.htm", params=params, auth=auth, timeout=(5, 15)))
        data = r.json()
        if data.get("status") not in ("OK", None):
            raise BridgeError(f"Domoticz: {data.get('message') or data.get('status')}")
        return data

    def list_devices(self) -> list[Device]:
        try:
            data = self._get(type="command", param="getdevices", filter="light", used="true")
        except Exception:
            data = self._get(type="devices", filter="light", used="true")
        return [Device(id=str(d["idx"]), name=d.get("Name", ""), state=as_bool(d.get("Status", "").split(" ")[0]),
                       kind=d.get("SwitchType", "")) for d in data.get("result") or []]

    def set_state(self, device_id: str, on: bool) -> None:
        self._get(type="command", param="switchlight", idx=device_id, switchcmd="On" if on else "Off")


@register
class IoBroker(Connector):
    type_id = "iobroker"
    title = "ioBroker"
    description = "Состояния ioBroker через адаптер simple-api"
    category = "universal"
    icon = "iobroker"
    manual_devices = True
    docs = "Установите адаптер <b>simple-api</b> (порт 8087). Укажите ID состояний, например <code>sonoff.0.PS5.POWER</code>."
    fields = [
        field("url", "Адрес simple-api", required=True, placeholder="http://192.168.1.40:8087"),
        field("devices", "Устройства", "table", columns=[
            col("name", "Название", required=True, placeholder="PS5-1"),
            col("state_id", "ID состояния", required=True, placeholder="sonoff.0.PS5.POWER"),
        ]),
    ]

    def _base(self) -> str:
        self.require("url")
        return self.settings["url"].strip().rstrip("/")

    def _probe(self, sid: str) -> bool | None:
        r = check_http(self.http.get(f"{self._base()}/getPlainValue/{sid}", timeout=(3, 6)))
        return as_bool(r.text.strip().strip('"'))

    def list_devices(self) -> list[Device]:
        out = []
        for i, r in enumerate(self.rows()):
            try:
                st, online = self._probe(r.get("state_id", "")), True
            except Exception:
                st, online = None, False
            out.append(Device(id=self.row_id(r, i), name=self.row_id(r, i), state=st, online=online))
        return out

    def set_state(self, device_id: str, on: bool) -> None:
        sid = self.row(device_id).get("state_id", "")
        check_http(self.http.get(f"{self._base()}/set/{sid}", params={"value": "true" if on else "false"}, timeout=(3, 6)))


@register
class Webhook(Connector):
    type_id = "webhook"
    title = "HTTP-запросы (вебхуки)"
    description = "Любое устройство или сервис, управляемый ссылкой: Node-RED, IFTTT, Homey, MajorDoMo, ESPHome и т.д."
    category = "universal"
    icon = "webhook"
    manual_devices = True
    docs = (
        "Для каждого устройства укажите ссылки включения и выключения. Необязательная ссылка статуса: "
        "если ответ содержит указанный текст — устройство считается включённым."
    )
    fields = [
        field("method", "HTTP-метод", "select", default="GET", options=[{"value": "GET", "label": "GET"}, {"value": "POST", "label": "POST"}]),
        field("headers", "Доп. заголовок (необязательно)", placeholder="Authorization: Bearer xxx"),
        field("devices", "Устройства", "table", columns=[
            col("name", "Название", required=True, placeholder="Xbox-1"),
            col("on_url", "Ссылка «включить»", required=True, placeholder="http://192.168.1.5/on"),
            col("off_url", "Ссылка «выключить»", required=True, placeholder="http://192.168.1.5/off"),
            col("status_url", "Ссылка статуса"),
            col("status_on", "Текст «включено»", placeholder='"ON"'),
        ]),
    ]

    def _headers(self) -> dict:
        raw = (self.settings.get("headers") or "").strip()
        if ":" in raw:
            k, v = raw.split(":", 1)
            return {k.strip(): v.strip()}
        return {}

    def _probe(self, r: dict) -> bool | None:
        url = (r.get("status_url") or "").strip()
        if not url:
            return None
        resp = check_http(self.http.get(url, headers=self._headers(), timeout=(3, 6)))
        needle = (r.get("status_on") or "").strip()
        return (needle in resp.text) if needle else as_bool(resp.text.strip())

    def list_devices(self) -> list[Device]:
        out = []
        for i, r in enumerate(self.rows()):
            try:
                st, online = self._probe(r), True
            except Exception:
                st, online = None, False
            out.append(Device(id=self.row_id(r, i), name=self.row_id(r, i), state=st, online=online))
        return out

    def test(self) -> str:
        devs = self.list_devices()
        if not devs:
            raise BridgeError("добавьте хотя бы одно устройство в таблицу")
        return f"Устройств в списке: {len(devs)} (ссылки проверяются кнопками «Вкл/Выкл»)"

    def set_state(self, device_id: str, on: bool) -> None:
        r = self.row(device_id)
        url = ((r.get("on_url") if on else r.get("off_url")) or "").strip()
        if not url:
            raise BridgeError("не указана ссылка")
        check_http(self.http.request(self.opt("method", "GET"), url, headers=self._headers(), timeout=(3, 10)))
