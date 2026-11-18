"""Tuya / Smart Life / Digma / многие розетки с AliExpress — Tuya Cloud OpenAPI."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid

from ..net import AuthError, BridgeError
from .base import Connector, Device, field, register

REGIONS = {
    "eu": "https://openapi.tuyaeu.com",
    "us": "https://openapi.tuyaus.com",
    "cn": "https://openapi.tuyacn.com",
    "in": "https://openapi.tuyain.com",
    "weu": "https://openapi-weaz.tuyaeu.com",
    "eus": "https://openapi-ueaz.tuyaus.com",
}
SWITCH_CODES = ("switch_1", "switch", "switch_led", "switch_on", "power", "switch_2")
# прочие логические команды, похожие на вкл/выкл (switch_usb1, power_switch, on_off…)
SWITCH_PREFIXES = ("switch", "power", "on_off", "led_switch")
MAX_FUNCTION_LOOKUPS = 30  # запросов списка команд за один опрос (лимиты Tuya API)

NO_DEVICES_HINT = (
    "Tuya не вернула ни одного устройства. Привяжите аккаунт приложения Smart Life/Tuya к облачному проекту "
    "(platform.tuya.com → проект → Devices → Link App Account) и выберите в программе тот же дата-центр, "
    "в котором устройства видны в проекте."
)


def _pick_code(status: dict) -> str:
    """Команда вкл/выкл по текущему состоянию устройства."""
    for c in SWITCH_CODES:
        if c in status:
            return c
    return next((c for c, v in status.items() if isinstance(v, bool) and str(c).lower().startswith(SWITCH_PREFIXES)), "")


@register
class Tuya(Connector):
    type_id = "tuya"
    title = "Tuya / Smart Life"
    description = "Розетки и реле Tuya, Smart Life, Digma, Moes, Zemismart и др. (облако Tuya)"
    category = "cloud"
    icon = "tuya"
    docs = (
        "<ol><li>Зарегистрируйтесь на <a href='https://platform.tuya.com' target='_blank'>platform.tuya.com</a> → Cloud → "
        "Development → <b>Create Cloud Project</b> (регион дата-центра — Central Europe).</li>"
        "<li>Скопируйте <b>Access ID</b> и <b>Access Secret</b> со страницы проекта.</li>"
        "<li>Вкладка Devices → Link App Account → отсканируйте QR-код в приложении Smart Life/Tuya.</li>"
        "<li>Убедитесь, что в Service API подключены «IoT Core» и «Authorization».</li></ol>"
    )
    fields = [
        field("access_id", "Access ID (Client ID)", required=True),
        field("access_secret", "Access Secret", "password", required=True),
        field("region", "Дата-центр", "select", default="eu",
              options=[{"value": k, "label": v} for k, v in {
                  "eu": "Центральная Европа (рекомендуется для РФ)", "weu": "Западная Европа", "us": "Запад США",
                  "eus": "Восток США", "cn": "Китай", "in": "Индия"}.items()]),
        field("switch_code", "Код команды (необязательно)", placeholder="switch_1",
              help="Обычно определяется автоматически"),
    ]

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._token = ""
        self._token_exp = 0.0
        self._codes: dict[str, str] = {}
        self._fn_codes: dict[str, str] = {}  # команда из списка функций устройства ("" — не нашлась)

    def _base(self) -> str:
        return REGIONS.get(self.opt("region", "eu"), REGIONS["eu"])

    def _sign(self, method: str, path: str, body: str, token: str = "") -> dict:
        self.require("access_id", "access_secret")
        cid = self.settings["access_id"].strip()
        t = str(int(time.time() * 1000))
        nonce = uuid.uuid4().hex
        content_hash = hashlib.sha256(body.encode()).hexdigest()
        string_to_sign = f"{method}\n{content_hash}\n\n{path}"
        msg = cid + token + t + nonce + string_to_sign
        sign = hmac.new(self.settings["access_secret"].strip().encode(), msg.encode(), hashlib.sha256).hexdigest().upper()
        h = {"client_id": cid, "sign": sign, "t": t, "nonce": nonce, "sign_method": "HMAC-SHA256",
             "Content-Type": "application/json"}
        if token:
            h["access_token"] = token
        return h

    def _request(self, method: str, path: str, body: dict | None = None, auth: bool = True) -> dict:
        raw = json.dumps(body) if body is not None else ""
        token = self._get_token() if auth else ""
        resp = self.http.request(method, self._base() + path, data=raw or None,
                                 headers=self._sign(method, path, raw, token), timeout=(5, 15))
        data = resp.json()
        if not data.get("success"):
            code = data.get("code")
            if code in (1010, 1011) and auth:  # токен истёк
                self._token = ""
            msg = f"Tuya: {data.get('msg')} (код {code})"
            if code in (1004, 1106, 2009, 1010, 1011):
                raise AuthError(msg)
            raise BridgeError(msg)
        return data.get("result")

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_exp:
            return self._token
        res = self._request("GET", "/v1.0/token?grant_type=1", auth=False)
        self._token = res["access_token"]
        self._token_exp = time.time() + int(res.get("expire_time", 3600)) - 120
        return self._token

    def _function_code(self, device_id: str) -> str:
        """Команда вкл/выкл из списка функций устройства (для нестандартных устройств)."""
        if device_id in self._fn_codes:
            return self._fn_codes[device_id]
        res = self._request("GET", f"/v1.0/iot-03/devices/{device_id}/functions") or {}
        codes = [str(f.get("code") or "") for f in res.get("functions") or [] if str(f.get("type", "")).lower() == "boolean"]
        code = next((c for c in SWITCH_CODES if c in codes), "") or next((c for c in codes if c.lower().startswith(SWITCH_PREFIXES)), "")
        self._fn_codes[device_id] = code
        return code

    def list_devices(self) -> list[Device]:
        out: list[Device] = []
        skipped: list[str] = []
        total = lookups = 0
        last = ""
        for _ in range(20):
            path = "/v1.0/iot-01/associated-users/devices?size=100" + (f"&last_row_key={last}" if last else "")
            res = self._request("GET", path) or {}
            for d in res.get("devices") or []:
                total += 1
                status = {s.get("code"): s.get("value") for s in d.get("status") or []}
                code = self.opt("switch_code") or _pick_code(status)
                if not code and (d["id"] in self._fn_codes or lookups < MAX_FUNCTION_LOOKUPS):
                    lookups += d["id"] not in self._fn_codes
                    try:
                        code = self._function_code(d["id"])
                    except AuthError:
                        raise
                    except BridgeError:
                        code = ""
                if not code:
                    skipped.append(d.get("name") or d["id"])
                    continue
                self._codes[d["id"]] = code
                val = status.get(code)
                out.append(Device(id=d["id"], name=d.get("name", ""), state=val if isinstance(val, bool) else None,
                                  kind=d.get("category", ""), online=bool(d.get("online", True))))
            if not res.get("has_more"):
                break
            last = res.get("last_row_key", "")
        if not total:
            self.note = NO_DEVICES_HINT
        elif skipped:
            names = ", ".join(skipped[:8]) + (f" и ещё {len(skipped) - 8}" if len(skipped) > 8 else "")
            self.note = (f"Tuya вернула устройств: {total}, без команды вкл/выкл пропущено: {len(skipped)} ({names}). "
                         "Если среди них есть розетки или реле — укажите «Код команды» в настройках "
                         "или включите для них в проекте Tuya режим управления «DP Instruction».")
        else:
            self.note = ""
        return out

    def set_state(self, device_id: str, on: bool) -> None:
        code = self.opt("switch_code") or self._codes.get(device_id)
        if not code:
            self.list_devices()
            code = self._codes.get(device_id, "switch_1")
        self._request("POST", f"/v1.0/iot-03/devices/{device_id}/commands", {"commands": [{"code": code, "value": bool(on)}]})
