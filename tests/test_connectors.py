import json

import pytest

from ssbridge import connectors
from ssbridge.connectors.base import as_bool
from ssbridge.connectors.mqtt import _match
from ssbridge.net import AuthError, BridgeError


class Resp:
    def __init__(self, data=None, status=200, text=None):
        self._data = data
        self.status_code = status
        self.text = text if text is not None else json.dumps(data)

    def json(self):
        if self._data is None:
            raise ValueError("no json")
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(response=self)


class FakeHTTP:
    """Подмена requests.Session: маршрутизация по подстроке URL."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def _find(self, method, url, **kw):
        self.calls.append((method, url, kw))
        for (m, part), resp in self.routes.items():
            if m == method and part in url:
                return resp(url, kw) if callable(resp) else resp
        raise AssertionError(f"нет маршрута {method} {url}")

    def get(self, url, **kw):
        return self._find("GET", url, **kw)

    def post(self, url, **kw):
        return self._find("POST", url, **kw)

    def request(self, method, url, **kw):
        return self._find(method, url, **kw)

    def close(self):
        pass


def make(type_id, settings):
    return connectors.create({"id": "x", "type": type_id, "name": type_id, "settings": settings})


def test_registry_has_all_systems():
    types = {t["type"] for t in connectors.schema()}
    assert {"yandex", "homeassistant", "tuya", "smartthings", "shelly", "tasmota", "sonoff", "mqtt",
            "openhab", "domoticz", "iobroker", "webhook"} <= types
    assert connectors.schema()[0]["type"] == "yandex"


def test_yandex_parses_on_off_capability():
    c = make("yandex", {"token": "t"})
    c.http = FakeHTTP({("GET", "/user/info"): Resp({"status": "ok", "rooms": [{"id": "r", "name": "Зал"}], "devices": [
        {"id": "1", "name": "ПС5", "room": "r", "type": "devices.types.socket",
         "capabilities": [{"type": "devices.capabilities.range"}, {"type": "devices.capabilities.on_off", "state": {"instance": "on", "value": True}}]},
        {"id": "2", "name": "Датчик", "capabilities": []},
    ]})})
    devs = c.list_devices()
    assert len(devs) == 1 and devs[0].state is True and devs[0].room == "Зал" and devs[0].kind == "socket"
    c.http = FakeHTTP({("POST", "/devices/actions"): Resp({"status": "ok", "devices": [{"capabilities": [{"state": {"action_result": {"status": "DONE"}}}]}]})})
    c.set_state("1", False)
    body = c.http.calls[0][2]["json"]
    assert body["devices"][0]["actions"][0]["state"]["value"] is False


def test_yandex_auth_error():
    c = make("yandex", {"token": "bad"})
    c.http = FakeHTTP({("GET", "/user/info"): Resp({"status": "error"}, status=401)})
    with pytest.raises(AuthError):
        c.list_devices()


def test_yandex_requires_token():
    with pytest.raises(BridgeError):
        make("yandex", {}).list_devices()


def test_homeassistant():
    c = make("homeassistant", {"url": "http://ha:8123/", "token": "t"})
    c.http = FakeHTTP({("GET", "/api/states"): Resp([
        {"entity_id": "switch.ps5", "state": "on", "attributes": {"friendly_name": "PS5"}},
        {"entity_id": "light.lamp", "state": "unavailable", "attributes": {}},
        {"entity_id": "sensor.temp", "state": "21"},
    ]), ("POST", "/api/services/switch/turn_off"): Resp([])})
    devs = {d.id: d for d in c.list_devices()}
    assert devs["switch.ps5"].state is True and devs["light.lamp"].state is None and "sensor.temp" not in devs
    c.set_state("switch.ps5", False)
    assert c.http.calls[-1][1] == "http://ha:8123/api/services/switch/turn_off"


def test_tasmota_and_shelly():
    t = make("tasmota", {"devices": [{"name": "TV", "address": "10.0.0.5", "channel": 0}]})
    t.http = FakeHTTP({("GET", "/cm"): lambda url, kw: Resp({"POWER": "ON"})})
    assert t.list_devices()[0].state is True
    t.set_state("TV", False)
    assert t.http.calls[-1][2]["params"]["cmnd"] == "Power Off"

    s = make("shelly", {"devices": [{"name": "PS", "address": "10.0.0.6", "channel": 0}]})
    s.http = FakeHTTP({("GET", "/shelly"): Resp({"gen": 2}), ("GET", "Switch.GetStatus"): Resp({"output": False}),
                       ("GET", "Switch.Set"): Resp({"was_on": False})})
    assert s.list_devices()[0].state is False
    s.set_state("PS", True)
    assert s.http.calls[-1][2]["params"] == {"id": 0, "on": "true"}


def test_local_offline_device_marked():
    t = make("tasmota", {"devices": [{"name": "TV", "address": "10.0.0.5"}]})

    def boom(url, kw):
        raise ConnectionError("down")
    t.http = FakeHTTP({("GET", "/cm"): boom})
    d = t.list_devices()[0]
    assert d.online is False and d.state is None
    with pytest.raises(BridgeError):
        t.test()


def test_webhook():
    w = make("webhook", {"devices": [{"name": "X", "on_url": "http://a/on", "off_url": "http://a/off", "status_url": "http://a/s", "status_on": "ON"}]})
    w.http = FakeHTTP({("GET", "http://a/s"): Resp(None, text='{"POWER":"ON"}'), ("GET", "http://a/o"): Resp(None, text="ok")})
    assert w.list_devices()[0].state is True
    w.set_state("X", False)
    assert w.http.calls[-1][1] == "http://a/off"


def test_tuya_signature_headers():
    c = make("tuya", {"access_id": "id", "access_secret": "sec"})
    h = c._sign("GET", "/v1.0/token?grant_type=1", "")
    assert h["client_id"] == "id" and len(h["sign"]) == 64 and h["sign"].isupper()


def _tuya(devices, functions=None, settings=None):
    """Коннектор Tuya с подменённым облаком: devices — ответ списка, functions — {id: [функции]}."""
    c = make("tuya", {"access_id": "id", "access_secret": "sec", **(settings or {})})
    fn_calls = []

    def fns(url, kw):
        dev = url.split("/devices/")[1].split("/")[0]
        fn_calls.append(dev)
        return Resp({"success": True, "result": {"functions": (functions or {}).get(dev, [])}})

    c.http = FakeHTTP({
        ("GET", "/v1.0/token"): Resp({"success": True, "result": {"access_token": "tok", "expire_time": 7200}}),
        ("GET", "/functions"): fns,
        ("GET", "/associated-users/devices"): Resp({"success": True, "result": {"devices": devices, "has_more": False}}),
        ("POST", "/commands"): Resp({"success": True, "result": True}),
    })
    return c, fn_calls


def test_tuya_no_devices_explains_why():
    c, _ = _tuya([])
    assert c.list_devices() == [] and "Link App Account" in c.note
    with pytest.raises(BridgeError, match="не вернула ни одного устройства"):
        c.test()


def test_tuya_finds_switch_codes_beyond_standard_list():
    c, calls = _tuya([
        {"id": "a", "name": "Розетка", "status": [{"code": "switch_1", "value": True}]},
        {"id": "b", "name": "Удлинитель USB", "status": [{"code": "switch_usb1", "value": False}, {"code": "countdown", "value": 0}]},
    ])
    devs = {d.id: d for d in c.list_devices()}
    assert devs["a"].state is True and devs["b"].state is False
    assert c.note == "" and calls == []
    c.set_state("b", True)
    assert json.loads(c.http.calls[-1][2]["data"])["commands"][0]["code"] == "switch_usb1"


def test_tuya_uses_device_functions_and_caches_them():
    c, calls = _tuya([{"id": "r", "name": "Реле VIP", "status": []}],
                     functions={"r": [{"code": "countdown_1", "type": "Integer"}, {"code": "switch_1", "type": "Boolean"}]})
    assert [d.name for d in c.list_devices()] == ["Реле VIP"]
    c.list_devices()
    assert calls == ["r"]  # список функций запрашивается один раз
    c.set_state("r", False)
    assert json.loads(c.http.calls[-1][2]["data"])["commands"][0]["code"] == "switch_1"


def test_tuya_reports_skipped_devices():
    c, calls = _tuya([
        {"id": "a", "name": "Розетка", "status": [{"code": "switch_1", "value": False}]},
        {"id": "t", "name": "Датчик температуры", "status": [{"code": "va_temperature", "value": 231}]},
    ])
    assert len(c.list_devices()) == 1
    assert "пропущено: 1" in c.note and "Датчик температуры" in c.note
    assert "найдено устройств: 1" in c.test()
    c2, _ = _tuya([{"id": "t", "name": "Датчик", "status": []}])
    with pytest.raises(BridgeError, match="без команды вкл/выкл"):
        c2.test()


def test_tuya_manual_switch_code_keeps_every_device():
    c, calls = _tuya([{"id": "x", "name": "Нестандартное", "status": []}], settings={"switch_code": "switch_1"})
    assert [d.id for d in c.list_devices()] == ["x"] and calls == [] and c.note == ""


def test_helpers():
    assert as_bool("ON") is True and as_bool("off") is False and as_bool("unavailable") is None
    assert _match('{"state":"ON"}', "ON") is True
    assert _match('{"state":"OFF"}', "ON") is False
    assert _match("on", "ON") is True
    assert _match("true", "ON") is True
