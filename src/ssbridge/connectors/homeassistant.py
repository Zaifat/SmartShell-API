"""Home Assistant — REST API. Через HA доступны Xiaomi/Aqara, Sber, Zigbee, HomeKit и сотни других."""
from __future__ import annotations

from ..net import BridgeError, check_http
from .base import Connector, Device, field, register

DOMAINS = ("switch", "light", "input_boolean", "fan", "media_player", "climate", "humidifier", "remote", "siren")


@register
class HomeAssistant(Connector):
    type_id = "homeassistant"
    title = "Home Assistant"
    description = "Универсальный шлюз: Xiaomi, Aqara, Sber, Zigbee, HomeKit, Google и сотни других систем"
    category = "universal"
    icon = "home"
    docs = (
        "<ol><li>В Home Assistant откройте профиль пользователя → вкладка «Безопасность».</li>"
        "<li>Внизу создайте <b>долгосрочный токен доступа</b> и скопируйте его.</li>"
        "<li>Адрес — как вы открываете HA в браузере, например <code>http://192.168.1.10:8123</code>.</li></ol>"
    )
    fields = [
        field("url", "Адрес Home Assistant", required=True, placeholder="http://homeassistant.local:8123"),
        field("token", "Долгосрочный токен", "password", required=True),
        field("verify_ssl", "Проверять SSL-сертификат", "bool", default=False),
    ]

    def _base(self) -> str:
        self.require("url", "token")
        return self.settings["url"].strip().rstrip("/")

    def _h(self) -> dict:
        return {"Authorization": f"Bearer {self.settings['token'].strip()}", "Content-Type": "application/json"}

    def test(self) -> str:
        resp = check_http(self.http.get(f"{self._base()}/api/", headers=self._h(), timeout=(5, 10), verify=bool(self.opt("verify_ssl"))))
        msg = resp.json().get("message", "")
        return f"{msg or 'OK'}, найдено устройств: {len(self.list_devices())}"

    def list_devices(self) -> list[Device]:
        resp = check_http(self.http.get(f"{self._base()}/api/states", headers=self._h(), timeout=(5, 20), verify=bool(self.opt("verify_ssl"))))
        out = []
        for s in resp.json():
            eid = s.get("entity_id", "")
            domain = eid.split(".", 1)[0]
            if domain not in DOMAINS:
                continue
            st = s.get("state")
            state = None if st in ("unavailable", "unknown", None) else st not in ("off", "standby", "idle")
            out.append(Device(id=eid, name=(s.get("attributes") or {}).get("friendly_name") or eid, state=state,
                              kind=domain, online=st != "unavailable"))
        return out

    def set_state(self, device_id: str, on: bool) -> None:
        domain = device_id.split(".", 1)[0]
        if domain not in DOMAINS:
            raise BridgeError(f"Home Assistant: тип {domain} не поддерживает вкл/выкл")
        svc = "turn_on" if on else "turn_off"
        check_http(self.http.post(f"{self._base()}/api/services/{domain}/{svc}", json={"entity_id": device_id},
                                  headers=self._h(), timeout=(5, 15), verify=bool(self.opt("verify_ssl"))))
