"""Клиент SmartShell (GraphQL).

* billing.smartshell.gg — API администратора (логин, список хостов, регистрация);
* host.smartshell.gg — API «шелла» хоста (виртуальные хосты для приставок).

Запросы к billing ограничиваются RateLimiter: по документации SmartShell
не более 20 запросов в минуту на один company_id.
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field

from . import __version__, journal
from .net import AuthError, BridgeError, RateLimiter, check_http, session

BILLING_URL = "https://billing.smartshell.gg/api/graphql"
HOST_URL = "https://host.smartshell.gg/api/graphql"

Q_LOGIN = "mutation login($input: LoginInput!) { login(input: $input) { access_token refresh_token expires_in } }"
Q_REFRESH = "mutation refreshToken($input: RefreshTokenInput!) { refreshToken(input: $input) { access_token refresh_token expires_in } }"
Q_CLUBS = "query userClubs($input: UserClubsInput) { userClubs(input: $input) { id name address } }"
Q_HOSTS = (
    "query hostGroups { hostGroups { id title hosts { id group_id alias in_service is_deleted online "
    "client_sessions { id status } } } }"
)
Q_REGISTER = (
    "mutation registerHost($input: RegisterHostInput!) { registerHost(input: $input) }"
)
Q_HOST_STATE = (
    'mutation { updateHostState(input: {cpu_temp: 0, disk_temp: 0, disk_status: {letter: "NA", total: 0, used: 0}, '
    'active_window: "SmartShell Bridge"}) { client_session { id } } }'
)
Q_HOST_START = (
    "mutation startHostSession($input: HostSessionInput!) { startHostSession(input: $input) { host_id } }"
)

ACTIVE_STATUSES = {"ACTIVE"}


@dataclass
class Host:
    id: int
    alias: str
    group_id: int
    group: str
    active: bool
    in_service: bool
    online: bool
    sessions: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "alias": self.alias, "group_id": self.group_id, "group": self.group,
            "active": self.active, "in_service": self.in_service, "online": self.online,
        }


_TRANSLATE = {
    "incorrect login or password": "неверный логин или пароль",
    "unauthenticated": "требуется авторизация",
    "too many requests": "слишком много запросов",
    "active host session not found": "сеанс хоста не найден",
}


def _gql_errors(data: dict) -> str | None:
    errs = data.get("errors") if isinstance(data, dict) else None
    if not errs:
        return None
    msgs = []
    for e in errs:
        m = str(e.get("message", e)) if isinstance(e, dict) else str(e)
        msgs.append(_TRANSLATE.get(m.strip().lower(), m))
    return "; ".join(msgs)


def _is_auth_message(msg: str) -> bool:
    m = msg.lower()
    return any(k in m for k in ("unauthenticated", "unauthorized", "token", "auth", "авториз", "доступ"))


class SmartShell:
    def __init__(self, login: str, password: str, company_id: str | int, user_agent: str = "", rpm: int = 15):
        self.login_name = (login or "").strip()
        self.password = password or ""
        self.company_id = str(company_id or "").strip()
        ua = user_agent or f"company_id={self.company_id}. SmartShellBridge/{__version__}"
        self.http = session(ua)
        self.limiter = RateLimiter(rpm)
        self._token: str | None = None
        self._refresh: str | None = None
        self._expires = 0.0
        self._lock = threading.RLock()

    # ------------------------------------------------------------ low level
    def _post(self, url: str, query: str, variables: dict | None = None, headers: dict | None = None,
              limited: bool = True) -> dict:
        if limited and url == BILLING_URL and not self.limiter.acquire(max_wait=45):
            raise BridgeError("превышен лимит запросов к SmartShell (20/мин), запрос отложен")
        resp = self.http.post(url, json={"query": query, "variables": variables or {}},
                              headers=headers or {}, timeout=(5, 20))
        if resp.status_code >= 500:
            raise BridgeError(f"SmartShell: ошибка сервера HTTP {resp.status_code}")
        if resp.status_code == 429:
            raise BridgeError("SmartShell: слишком много запросов (HTTP 429)")
        try:
            data = resp.json()
        except ValueError:
            check_http(resp)
            raise BridgeError("SmartShell вернул некорректный ответ")
        return data

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.ensure_token()}"}

    # ------------------------------------------------------------ auth
    @property
    def configured(self) -> bool:
        return bool(self.login_name and self.password and self.company_id)

    def authenticate(self) -> str:
        if not self.configured:
            raise AuthError("SmartShell: не заполнены логин, пароль или ID клуба")
        try:
            cid = int(self.company_id)
        except ValueError:
            raise AuthError("SmartShell: ID клуба должен быть числом")
        data = self._post(BILLING_URL, Q_LOGIN, {"input": {"login": self.login_name, "password": self.password, "company_id": cid}})
        err = _gql_errors(data)
        tok = ((data.get("data") or {}).get("login") or {})
        if err or not tok.get("access_token"):
            raise AuthError(f"SmartShell: не удалось войти — {err or 'пустой токен'}")
        self._store(tok)
        journal.info("SmartShell: выполнен вход, токен получен", "smartshell")
        return self._token

    def _store(self, tok: dict) -> None:
        self._token = tok["access_token"]
        self._refresh = tok.get("refresh_token")
        self._expires = time.time() + float(tok.get("expires_in") or 3600) - 300

    def _try_refresh(self) -> bool:
        if not self._refresh:
            return False
        try:
            data = self._post(BILLING_URL, Q_REFRESH, {"input": {"refresh_token": self._refresh}})
            tok = ((data.get("data") or {}).get("refreshToken") or {})
            if tok.get("access_token"):
                self._store(tok)
                journal.debug("SmartShell: токен обновлён", "smartshell")
                return True
        except Exception as e:
            journal.debug(f"SmartShell: не удалось обновить токен: {e}", "smartshell")
        return False

    def ensure_token(self) -> str:
        with self._lock:
            if self._token and time.time() < self._expires:
                return self._token
            if self._token and self._try_refresh():
                return self._token
            return self.authenticate()

    def invalidate(self) -> None:
        with self._lock:
            self._token = None

    def _query(self, query: str, variables: dict | None = None) -> dict:
        """Запрос с авторизацией и одной повторной попыткой при ошибке токена."""
        for attempt in range(2):
            data = self._post(BILLING_URL, query, variables, self._auth_headers())
            err = _gql_errors(data)
            if not err:
                return data.get("data") or {}
            if attempt == 0 and (_is_auth_message(err) or not data.get("data")):
                self.invalidate()
                continue
            raise BridgeError(f"SmartShell: {err}")
        raise BridgeError("SmartShell: ошибка авторизации")

    # ------------------------------------------------------------ public
    def clubs(self) -> list[dict]:
        data = self._post(BILLING_URL, Q_CLUBS, {"input": {"login": self.login_name, "password": self.password}})
        err = _gql_errors(data)
        if err:
            raise AuthError(f"SmartShell: {err}")
        return (data.get("data") or {}).get("userClubs") or []

    def hosts(self) -> tuple[list[Host], list[dict]]:
        data = self._query(Q_HOSTS)
        groups = data.get("hostGroups")
        if groups is None:
            raise BridgeError("SmartShell: пустой ответ на запрос списка хостов")
        hosts: list[Host] = []
        group_list = []
        for g in groups:
            group_list.append({"id": g.get("id"), "title": g.get("title")})
            for h in g.get("hosts") or []:
                if h.get("is_deleted"):
                    continue
                sessions = h.get("client_sessions") or []
                active = any((s.get("status") or "ACTIVE") in ACTIVE_STATUSES for s in sessions)
                hosts.append(Host(
                    id=int(h["id"]), alias=str(h.get("alias") or ""), group_id=int(h.get("group_id") or g.get("id") or 0),
                    group=str(g.get("title") or ""), active=active, in_service=bool(h.get("in_service")),
                    online=bool(h.get("online")), sessions=sessions,
                ))
        return hosts, group_list

    def register_host(self, alias: str, group_id: int) -> str:
        """Создать хост (для приставки без шелла). Возвращает токен хоста."""
        t = int(time.time() * 1000)
        mac = "FF-FE-" + "-".join(f"{(t >> s) & 0xFF:02X}" for s in (24, 16, 8, 0))
        data = self._query(Q_REGISTER, {"input": {"group_id": int(group_id), "mac_addr": mac, "dns_name": "ssbridge", "alias": alias}})
        token = data.get("registerHost")
        if not token:
            raise BridgeError("SmartShell: хост не создан (пустой ответ)")
        journal.success(f"SmartShell: на карту клуба добавлен хост «{alias}»", "smartshell")
        return token

    def host_keepalive(self, host_token: str) -> None:
        """Поддерживать виртуальный хост «в сети», как это делает шелл."""
        headers = {"X-Host": host_token}
        data = self._post(HOST_URL, Q_HOST_STATE, headers=headers, limited=False)
        if (data.get("data") or {}).get("updateHostState") is not None:
            return
        err = _gql_errors(data) or ""
        if "session not found" in err.lower() or "host session" in err.lower() or "сеанс хоста" in err.lower():
            start = self._post(HOST_URL, Q_HOST_START, {"input": {
                "processor": "N/A", "ram": "N/A", "video": "N/A", "disc": "N/A",
                "shell_version": f"SmartShell Bridge {__version__}"}}, headers=headers, limited=False)
            if ((start.get("data") or {}).get("startHostSession") or {}).get("host_id"):
                data = self._post(HOST_URL, Q_HOST_STATE, headers=headers, limited=False)
                if (data.get("data") or {}).get("updateHostState") is not None:
                    return
            err = _gql_errors(start) or _gql_errors(data) or "нет ответа"
        raise BridgeError(f"виртуальный хост: {err or 'неизвестная ошибка'}")


def pretty(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)
