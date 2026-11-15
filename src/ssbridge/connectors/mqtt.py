"""MQTT — Zigbee2MQTT, Wiren Board, ESPHome, Tasmota-MQTT и любые устройства с MQTT."""
from __future__ import annotations

import json
import threading
import time

from ..net import BridgeError
from .base import Connector, Device, col, field, register

try:
    import paho.mqtt.client as paho
except ImportError:  # pragma: no cover
    paho = None


def _match(payload: str, on_value: str) -> bool | None:
    payload = payload.strip()
    on_value = (on_value or "ON").strip()
    if payload == on_value:
        return True
    try:
        data = json.loads(payload)
    except ValueError:
        data = None
    if isinstance(data, dict):
        for k in ("state", "State", "POWER", "power", "value", "on"):
            if k in data:
                v = data[k]
                if isinstance(v, bool):
                    return v
                return str(v).strip().lower() == on_value.lower()
        return None
    if isinstance(data, bool):
        return data
    return payload.lower() == on_value.lower()


@register
class MQTT(Connector):
    type_id = "mqtt"
    title = "MQTT"
    description = "Zigbee2MQTT, Wiren Board, ESPHome, Tasmota (MQTT) — любые устройства через брокер MQTT"
    category = "universal"
    icon = "mqtt"
    manual_devices = True
    docs = (
        "Укажите брокер и для каждого устройства — топик команды и значения. "
        "Пример для Zigbee2MQTT: топик <code>zigbee2mqtt/Розетка PS5/set</code>, вкл <code>{\"state\":\"ON\"}</code>, "
        "выкл <code>{\"state\":\"OFF\"}</code>, топик состояния <code>zigbee2mqtt/Розетка PS5</code>, значение «ON»."
    )
    fields = [
        field("host", "Адрес брокера", required=True, placeholder="192.168.1.10"),
        field("port", "Порт", "number", default=1883),
        field("username", "Логин"),
        field("password", "Пароль", "password"),
        field("tls", "TLS (шифрование)", "bool", default=False),
        field("devices", "Устройства", "table", columns=[
            col("name", "Название", required=True, placeholder="PS5-1"),
            col("command_topic", "Топик команды", required=True, placeholder="zigbee2mqtt/ps5/set"),
            col("payload_on", "Вкл", default="ON"),
            col("payload_off", "Выкл", default="OFF"),
            col("state_topic", "Топик состояния", placeholder="zigbee2mqtt/ps5"),
            col("state_on", "Значение «включено»", default="ON"),
        ]),
    ]

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._client = None
        self._connected = threading.Event()
        self._states: dict[str, str] = {}
        self._error = ""

    def _ensure(self):
        if paho is None:
            raise BridgeError("библиотека MQTT недоступна")
        self.require("host")
        if self._client is not None and self._connected.is_set():
            return self._client
        if self._client is None:
            c = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id=f"ssbridge-{self.id}-{int(time.time())}")
            if self.settings.get("username"):
                c.username_pw_set(self.settings["username"], self.settings.get("password") or None)
            if self.opt("tls"):
                c.tls_set()
            c.on_connect = self._on_connect
            c.on_disconnect = lambda *a, **k: self._connected.clear()
            c.on_message = self._on_message
            c.reconnect_delay_set(1, 30)
            try:
                c.connect_async(self.settings["host"].strip(), int(self.opt("port", 1883) or 1883), keepalive=30)
                c.loop_start()
            except Exception as e:
                raise BridgeError(f"MQTT: не удалось подключиться — {e}")
            self._client = c
        if not self._connected.wait(8):
            raise BridgeError(f"MQTT: нет подключения к брокеру {self.settings['host']} {self._error}".strip())
        return self._client

    def _on_connect(self, client, userdata, flags, reason, properties=None):
        if getattr(reason, "is_failure", False):
            self._error = f"({reason})"
            return
        self._connected.set()
        for r in self.rows():
            if (r.get("state_topic") or "").strip():
                client.subscribe(r["state_topic"].strip())

    def _on_message(self, client, userdata, msg):
        try:
            self._states[msg.topic] = msg.payload.decode("utf-8", "replace")
        except Exception:
            pass

    def _state(self, r: dict) -> bool | None:
        topic = (r.get("state_topic") or "").strip()
        if not topic or topic not in self._states:
            return None
        return _match(self._states[topic], r.get("state_on") or "ON")

    def list_devices(self) -> list[Device]:
        self._ensure()
        return [Device(id=self.row_id(r, i), name=self.row_id(r, i), state=self._state(r), kind="mqtt")
                for i, r in enumerate(self.rows())]

    def test(self) -> str:
        devs = self.list_devices()
        return f"Брокер подключён, устройств в списке: {len(devs)}"

    def set_state(self, device_id: str, on: bool) -> None:
        r = self.row(device_id)
        c = self._ensure()
        payload = (r.get("payload_on") or "ON") if on else (r.get("payload_off") or "OFF")
        info = c.publish(r["command_topic"].strip(), payload, qos=1)
        info.wait_for_publish(5)
        if not info.is_published():
            raise BridgeError("MQTT: сообщение не доставлено брокеру")

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass
            self._client = None
        super().close()
