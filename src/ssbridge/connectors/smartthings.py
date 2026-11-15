"""Samsung SmartThings — облачный API api.smartthings.com."""
from __future__ import annotations

from ..net import check_http
from .base import Connector, Device, field, register

API = "https://api.smartthings.com/v1"


@register
class SmartThings(Connector):
    type_id = "smartthings"
    title = "Samsung SmartThings"
    description = "Телевизоры Samsung, розетки и устройства, подключённые к SmartThings"
    category = "cloud"
    icon = "smartthings"
    docs = (
        "<ol><li>Откройте <a href='https://account.smartthings.com/tokens' target='_blank'>account.smartthings.com/tokens</a>.</li>"
        "<li>Создайте Personal Access Token с правами <b>Devices: List, See, Control</b>.</li>"
        "<li>Вставьте токен в поле ниже.</li></ol>"
    )
    fields = [field("token", "Personal Access Token", "password", required=True)]

    def _h(self) -> dict:
        self.require("token")
        return {"Authorization": f"Bearer {self.settings['token'].strip()}"}

    def list_devices(self) -> list[Device]:
        out = []
        url = f"{API}/devices?capability=switch"
        for _ in range(10):
            data = check_http(self.http.get(url, headers=self._h(), timeout=(5, 15))).json()
            for d in data.get("items") or []:
                out.append(Device(id=d["deviceId"], name=d.get("label") or d.get("name") or d["deviceId"],
                                  kind=(d.get("deviceTypeName") or "")))
            url = ((data.get("_links") or {}).get("next") or {}).get("href")
            if not url:
                break
        return out

    def _state(self, device_id: str) -> bool | None:
        data = check_http(self.http.get(f"{API}/devices/{device_id}/components/main/capabilities/switch/status",
                                        headers=self._h(), timeout=(5, 10))).json()
        v = (data.get("switch") or {}).get("value")
        return None if v is None else v == "on"

    def get_states(self, device_ids: list[str]) -> dict[str, bool | None]:
        res = {}
        for i in device_ids:
            try:
                res[i] = self._state(i)
            except Exception:
                res[i] = None
        return res

    def set_state(self, device_id: str, on: bool) -> None:
        body = {"commands": [{"component": "main", "capability": "switch", "command": "on" if on else "off"}]}
        check_http(self.http.post(f"{API}/devices/{device_id}/commands", json=body, headers=self._h(), timeout=(5, 15)))
