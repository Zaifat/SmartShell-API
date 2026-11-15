"""Яндекс Умный дом (Алиса) — облачный API api.iot.yandex.net."""
from __future__ import annotations

from ..net import BridgeError, check_http
from .base import Connector, Device, field, register

API = "https://api.iot.yandex.net/v1.0"
ON_OFF = "devices.capabilities.on_off"


@register
class Yandex(Connector):
    type_id = "yandex"
    title = "Яндекс Умный дом"
    description = "Розетки, лампы, ТВ и любые устройства «Умного дома с Алисой»"
    category = "cloud"
    icon = "yandex"
    docs = (
        "<ol><li>Откройте <a href='https://oauth.yandex.ru/client/new' target='_blank'>oauth.yandex.ru</a> и создайте приложение "
        "(платформа «Веб-сервисы», Redirect URI: <code>https://oauth.yandex.ru/verification_code</code>).</li>"
        "<li>В доступах выберите <b>Умный дом: просмотр (iot:view)</b> и <b>управление (iot:control)</b>.</li>"
        "<li>Скопируйте ClientID приложения и вставьте его в поле ниже — появится ссылка для получения токена.</li>"
        "<li>Перейдите по ссылке, разрешите доступ и вставьте полученный токен в поле «OAuth-токен».</li></ol>"
    )
    fields = [
        field("client_id", "ClientID приложения (необязательно)", help="Нужен только чтобы получить токен по ссылке"),
        field("token", "OAuth-токен", "password", required=True),
    ]

    def _headers(self) -> dict:
        self.require("token")
        return {"Authorization": f"Bearer {self.settings['token'].strip()}"}

    def list_devices(self) -> list[Device]:
        resp = check_http(self.http.get(f"{API}/user/info", headers=self._headers(), timeout=(5, 15)))
        data = resp.json()
        if data.get("status") != "ok":
            raise BridgeError(f"Яндекс: {data.get('message') or data.get('status')}")
        rooms = {r.get("id"): r.get("name", "") for r in data.get("rooms") or []}
        out = []
        for d in data.get("devices") or []:
            cap = next((c for c in d.get("capabilities") or [] if c.get("type") == ON_OFF), None)
            if cap is None:
                continue
            state = (cap.get("state") or {}).get("value")
            out.append(Device(
                id=d["id"], name=d.get("name", ""), state=state if isinstance(state, bool) else None,
                room=rooms.get(d.get("room"), ""), kind=(d.get("type") or "").replace("devices.types.", ""),
                online=d.get("state", "online") != "offline",
            ))
        return out

    def set_state(self, device_id: str, on: bool) -> None:
        body = {"devices": [{"id": device_id, "actions": [{"type": ON_OFF, "state": {"instance": "on", "value": bool(on)}}]}]}
        resp = check_http(self.http.post(f"{API}/devices/actions", json=body, headers=self._headers(), timeout=(5, 15)))
        data = resp.json()
        if data.get("status") != "ok":
            raise BridgeError(f"Яндекс: {data.get('message') or data.get('status')}")
        for dev in data.get("devices") or []:
            for cap in dev.get("capabilities") or []:
                res = ((cap.get("state") or {}).get("action_result") or {})
                if res.get("status") == "ERROR":
                    raise BridgeError(f"Яндекс: устройство не выполнило команду ({res.get('error_message') or res.get('error_code')})")
