"""Встроенный веб-сервер панели управления (без внешних зависимостей).

Безопасность:
* по умолчанию слушает только 127.0.0.1;
* доступ из локальной сети включается в настройках и требует PIN-код;
* изменяющие запросы требуют заголовок X-SSB (защита от CSRF с чужих сайтов);
* проверка заголовка Host защищает от DNS-rebinding.
"""
from __future__ import annotations

import hmac
import json
import mimetypes
import re
import secrets as pysecrets
import sys
import threading
import time
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import APP_NAME, __version__, connectors, journal, paths, winsys
from .config import MASK, Config, mask_tree, new_id, unmask_tree
from .net import BridgeError, describe
from .smartshell import SmartShell

LOCAL_HOSTS = {"127.0.0.1", "localhost", "[::1]", "::1"}


class Api:
    """Обработчики API (отделены от HTTP для удобства тестирования)."""

    def __init__(self, app):
        self.app = app
        self.config: Config = app.config
        self.engine = app.engine

    # ---------- общее
    def get_state(self, q, body):
        st = self.engine.status()
        st["version"] = __version__
        st["autostart"] = winsys.autostart_enabled()
        st["wizard_done"] = bool(self.config.get("wizard_done"))
        st["config_warning"] = self.config.load_error
        st["telegram"] = bool(self.app.notifier and self.app.notifier.enabled())
        return st

    def get_config(self, q, body):
        snap = self.config.snapshot()
        snap.pop("virtual_hosts", None)
        snap["virtual_hosts"] = [{"host_id": v["host_id"], "alias": v.get("alias")} for v in self.config.virtual_hosts()]
        snap["data_dir"] = str(paths.data_dir())
        return mask_tree(snap)

    def post_general(self, q, body):
        old = self.config.get("general")
        new = unmask_tree({k: v for k, v in body.items() if k in old}, old)
        if "poll_interval" in new:
            new["poll_interval"] = max(5, min(600, int(new["poll_interval"] or 10)))
        if "max_billing_rpm" in new:
            new["max_billing_rpm"] = max(3, min(19, int(new["max_billing_rpm"] or 15)))
        if "web_port" in new:
            new["web_port"] = max(1024, min(65535, int(new["web_port"] or 8765)))
        self.config.update("general", new)
        if "autostart" in body:
            winsys.set_autostart(bool(body["autostart"]))
        journal.info("Общие настройки сохранены", "config")
        self.engine.run_now()
        return {"ok": True, "restart_needed": any(k in new and new[k] != old.get(k) for k in ("web_port", "allow_lan"))}

    def post_notify(self, q, body):
        old = self.config.get("notify")
        self.config.update("notify", unmask_tree({k: v for k, v in body.items() if k in old}, old))
        journal.info("Настройки уведомлений сохранены", "config")
        return {"ok": True}

    def post_notify_test(self, q, body):
        self.app.notifier.send_now("SmartShell Bridge: тестовое уведомление ✅")
        return {"ok": True, "message": "Сообщение отправлено"}

    def post_wizard_done(self, q, body):
        self.config.update("wizard_done", True)
        return {"ok": True}

    # ---------- SmartShell
    def _ss_from_body(self, body) -> SmartShell:
        old = self.config.get("smartshell")
        data = unmask_tree(body, old)
        return SmartShell(data.get("login", ""), data.get("password", ""), data.get("company_id", "") or "0",
                          data.get("user_agent", ""))

    def post_smartshell_clubs(self, q, body):
        ss = self._ss_from_body(body)
        if not ss.login_name or not ss.password:
            raise BridgeError("введите логин и пароль SmartShell")
        clubs = ss.clubs()
        if not clubs:
            raise BridgeError("клубы не найдены — проверьте логин и пароль")
        return {"clubs": clubs}

    def post_smartshell_test(self, q, body):
        ss = self._ss_from_body(body)
        ss.authenticate()
        hosts, groups = ss.hosts()
        return {"ok": True, "message": f"Вход выполнен. Хостов: {len(hosts)}, групп: {len(groups)}, активных сеансов: {sum(h.active for h in hosts)}"}

    def post_smartshell(self, q, body):
        old = self.config.get("smartshell")
        new = unmask_tree({k: v for k, v in body.items() if k in old}, old)
        new["company_id"] = str(new.get("company_id", "")).strip()
        self.config.update("smartshell", new)
        journal.info("Настройки SmartShell сохранены", "config")
        self.engine.run_now()
        return {"ok": True}

    def get_hosts(self, q, body):
        if q.get("refresh") or not self.engine.hosts or time.time() - self.engine.hosts_ts > 60:
            self.engine.smartshell()
            self.engine.refresh_hosts()
        vh = {v["host_id"] for v in self.config.virtual_hosts()}
        return {
            "hosts": sorted([dict(h.to_dict(), virtual=h.id in vh) for h in self.engine.hosts.values()],
                            key=lambda h: (h["group"], _natural(h["alias"]))),
            "groups": self.engine.groups,
        }

    def post_virtual_host(self, q, body):
        alias = (body.get("alias") or "").strip()
        if not alias:
            raise BridgeError("укажите название хоста")
        ss = self.engine.smartshell()
        self.engine.refresh_hosts()
        if any(h.alias.lower() == alias.lower() for h in self.engine.hosts.values()):
            raise BridgeError(f"хост «{alias}» уже есть на карте клуба")
        group_id = body.get("group_id") or (self.engine.groups[0]["id"] if self.engine.groups else None)
        if not group_id:
            raise BridgeError("в SmartShell нет ни одной группы хостов")
        token = ss.register_host(alias, int(group_id))
        self.engine.refresh_hosts()
        host = next((h for h in self.engine.hosts.values() if h.alias == alias), None)
        if not host:
            raise BridgeError("хост создан, но не найден в списке — обновите страницу")
        self.config.add_virtual_host(host.id, alias, token)
        try:
            ss.host_keepalive(token)
        except Exception as e:
            journal.warning(f"Хост «{alias}» создан, но не вышел в сеть: {describe(e)}", "smartshell")
        binding = None
        if body.get("connector_id") and body.get("device_id"):
            binding, _ = self.config.add_binding({"host_id": host.id, "host_alias": host.alias, **{
                k: body[k] for k in ("connector_id", "device_id", "device_name") if k in body}})
            journal.success(f"Привязка: {host.alias} → {binding['device_name'] or binding['device_id']}", "config")
            self.engine.run_now()
        return {"ok": True, "host": host.to_dict(), "binding": binding}

    def delete_virtual_host(self, q, body):
        self.config.remove_virtual_host(int(body.get("host_id")))
        journal.info("Виртуальный хост удалён из программы (с карты клуба удалите его в SmartShell)", "smartshell")
        return {"ok": True}

    # ---------- системы умного дома
    def get_connector_types(self, q, body):
        return {"types": connectors.schema()}

    def post_connector(self, q, body):
        conf = {
            "id": body.get("id") or "",
            "type": body.get("type"),
            "name": (body.get("name") or "").strip() or connectors.REGISTRY[body["type"]].title,
            "enabled": bool(body.get("enabled", True)),
            "settings": body.get("settings") or {},
        }
        if conf["type"] not in connectors.REGISTRY:
            raise BridgeError("неизвестный тип системы")
        saved = self.config.upsert_connector(conf)
        journal.info(f"Сохранена система умного дома «{saved['name']}»", "config")
        self.engine.run_now()
        return {"ok": True, "connector": mask_tree(saved)}

    def delete_connector(self, q, body):
        conf = self.config.connector(body.get("id"))
        self.config.delete_connector(body.get("id"))
        journal.info(f"Удалена система «{(conf or {}).get('name')}» и её привязки", "config")
        return {"ok": True}

    def _conn_for(self, body):
        if body.get("settings") is not None and body.get("type"):
            old = self.config.connector(body.get("id") or "") or {}
            conf = {"id": body.get("id") or "test", "type": body["type"], "name": body.get("name") or "",
                    "settings": unmask_tree(body["settings"], old.get("settings") or {})}
            return connectors.create(conf), True
        return self.engine.connector(body.get("id") or q.get("id", "")), False

    def post_connector_test(self, q, body):
        conn, temp = self._conn_for(body)
        try:
            with conn.lock:
                msg = conn.test()
            journal.success(f"Проверка «{conn.name}»: {msg}", "devices")
            return {"ok": True, "message": msg}
        except Exception as e:
            journal.warning(f"Проверка «{conn.name}»: {describe(e)}", "devices")
            raise
        finally:
            if temp:
                conn.close()

    def post_connector_devices(self, q, body):
        conn, temp = self._conn_for(body)
        try:
            with conn.lock:
                devs = conn.list_devices()
            return {"devices": sorted([d.to_dict() for d in devs], key=lambda d: _natural(d["name"]))}
        finally:
            if temp:
                conn.close()

    def post_device_set(self, q, body):
        on = bool(body.get("on"))
        if body.get("binding_id"):
            b = next((x for x in self.config.bindings() if x["id"] == body["binding_id"]), None)
            if not b:
                raise BridgeError("привязка не найдена")
            self.engine.command(b, on, reason="ручное управление из панели (авто-синхронизация приостановлена на 5 мин)", manual=True)
        else:
            conn = self.engine.connector(body.get("connector_id"))
            with conn.lock:
                conn.set_state(body.get("device_id"), on)
            journal.info(f"Ручное управление: «{body.get('device_name') or body.get('device_id')}» {'включено' if on else 'выключено'}", "devices")
        return {"ok": True}

    def post_binding_release(self, q, body):
        bs = self.engine.bstate.get(body.get("binding_id"))
        if bs:
            bs.hold_until = 0
        self.engine.run_now()
        return {"ok": True}

    # ---------- привязки
    def post_bindings(self, q, body):
        items = []
        for b in body.get("bindings") or []:
            if not b.get("connector_id") or not b.get("device_id") or not (b.get("host_id") or b.get("host_alias")):
                continue
            items.append({
                "id": b.get("id") or new_id("b"),
                "host_id": b.get("host_id"), "host_alias": b.get("host_alias", ""),
                "connector_id": b["connector_id"], "device_id": b["device_id"], "device_name": b.get("device_name", ""),
                "enabled": bool(b.get("enabled", True)), "off_delay": max(0, int(b.get("off_delay") or 0)),
                "invert": bool(b.get("invert")), "on_in_service": bool(b.get("on_in_service")),
            })
        self.config.set_bindings(items)
        journal.info(f"Привязки сохранены ({len(items)})", "config")
        self.engine.run_now()
        return {"ok": True, "count": len(items)}

    def post_auto_match(self, q, body):
        """Найти пары «хост SmartShell ↔ устройство» с одинаковыми названиями."""
        self.engine.smartshell()
        self.engine.refresh_hosts()
        existing = {(b.get("connector_id"), b.get("device_id")) for b in self.config.bindings()}
        bound_hosts = {str(b.get("host_id")) for b in self.config.bindings()}
        hosts = {_norm(h.alias): h for h in self.engine.hosts.values()}
        found = []
        for conf in self.config.connectors():
            try:
                conn = self.engine.connector(conf["id"])
                with conn.lock:
                    devs = conn.list_devices()
            except Exception as e:
                journal.warning(f"Автоподбор: «{conf.get('name')}» недоступна — {describe(e)}", "config")
                continue
            for d in devs:
                h = hosts.get(_norm(d.name))
                if h and (conf["id"], d.id) not in existing and str(h.id) not in bound_hosts:
                    found.append({"id": new_id("b"), "host_id": h.id, "host_alias": h.alias, "connector_id": conf["id"],
                                  "device_id": d.id, "device_name": d.name, "enabled": True, "off_delay": 0,
                                  "invert": False, "on_in_service": False})
        return {"matches": found}

    # ---------- хосты и привязки (точечные операции)
    def get_devices_all(self, q, body):
        """Все устройства всех включённых систем (параллельно, с кэшем 20 с)."""
        from concurrent.futures import ThreadPoolExecutor
        cache = getattr(self, "_dev_cache", None)
        if cache is None:
            cache = self._dev_cache = {}
        confs = [c for c in self.config.connectors() if c.get("enabled", True)]
        now = time.time()

        def load(conf):
            sig = json.dumps(conf, sort_keys=True, ensure_ascii=False)
            hit = cache.get(conf["id"])
            if hit and not q.get("refresh") and now - hit[0] < 20 and hit[1] == sig:
                return hit[2]
            res = {"id": conf["id"], "name": conf.get("name"), "type": conf.get("type"), "ok": True, "error": "", "devices": []}
            try:
                conn = self.engine.connector(conf["id"])
                with conn.lock:
                    res["devices"] = sorted([d.to_dict() for d in conn.list_devices()], key=lambda d: _natural(d["name"]))
            except Exception as e:
                res["ok"], res["error"] = False, describe(e)
            cache[conf["id"]] = (time.time(), sig, res)
            return res

        if not confs:
            return {"systems": []}
        with ThreadPoolExecutor(max_workers=min(6, len(confs))) as ex:
            return {"systems": list(ex.map(load, confs))}

    def _check_binding_target(self, body):
        if not self.config.connector(body.get("connector_id") or ""):
            raise BridgeError("система умного дома не найдена")
        if not body.get("device_id"):
            raise BridgeError("не выбрано устройство")
        if not (body.get("host_id") or body.get("host_alias")):
            raise BridgeError("не выбран хост")

    def post_binding_add(self, q, body):
        self._check_binding_target(body)
        b, created = self.config.add_binding(body)
        if created:
            journal.success(f"Привязка: {b['host_alias']} → {b['device_name'] or b['device_id']}", "config")
            self.engine.run_now()
        return {"ok": True, "binding": b, "created": created}

    def post_bindings_add_many(self, q, body):
        added = 0
        for item in body.get("items") or []:
            try:
                self._check_binding_target(item)
            except BridgeError:
                continue
            _, created = self.config.add_binding(item)
            added += created
        if added:
            journal.success(f"Добавлено привязок: {added}", "config")
            self.engine.run_now()
        return {"ok": True, "added": added}

    def post_binding_update(self, q, body):
        b = self.config.update_binding(body.get("id", ""), body)
        self.engine.run_now()
        return {"ok": True, "binding": b}

    def post_binding_delete(self, q, body):
        b = next((x for x in self.config.bindings() if x["id"] == body.get("id")), None)
        self.config.delete_binding(body.get("id", ""))
        if b:
            journal.info(f"Привязка удалена: {b.get('host_alias')} → {b.get('device_name') or b.get('device_id')}", "config")
        return {"ok": True}

    # ---------- управление
    def post_engine(self, q, body):
        action = body.get("action")
        if action == "pause":
            self.engine.set_paused(True)
        elif action == "resume":
            self.engine.set_paused(False)
        elif action == "run":
            self.engine.run_now()
        return {"ok": True, "paused": self.engine.paused}

    def post_selftest(self, q, body):
        return {"checks": self.engine.self_test()}

    def get_logs(self, q, body):
        after = int(q.get("after", 0) or 0)
        return {"items": journal.ring.since(after, q.get("level"), int(q.get("limit", 500) or 500))}

    def post_open_url(self, q, body):
        winsys.open_url(str(body.get("url") or ""))
        return {"ok": True}

    def post_open_logs(self, q, body):
        winsys.open_folder(paths.logs_dir())
        return {"ok": True}


def _norm(s: str) -> str:
    """Нормализация названия: регистр, пробелы, похожие латиница/кириллица."""
    s = (s or "").strip().lower().replace("ё", "е")
    lat2cyr = str.maketrans({"a": "а", "b": "в", "e": "е", "k": "к", "m": "м", "h": "н", "o": "о", "p": "р",
                             "c": "с", "t": "т", "y": "у", "x": "х"})
    s = s.translate(lat2cyr)
    return re.sub(r"[\s_\-\.]+", "", s)


def _natural(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s or "")]


ROUTES = {
    ("GET", "/api/state"): "get_state",
    ("GET", "/api/config"): "get_config",
    ("POST", "/api/general"): "post_general",
    ("POST", "/api/notify"): "post_notify",
    ("POST", "/api/notify/test"): "post_notify_test",
    ("POST", "/api/wizard/done"): "post_wizard_done",
    ("POST", "/api/smartshell/clubs"): "post_smartshell_clubs",
    ("POST", "/api/smartshell/test"): "post_smartshell_test",
    ("POST", "/api/smartshell"): "post_smartshell",
    ("GET", "/api/hosts"): "get_hosts",
    ("POST", "/api/hosts/virtual"): "post_virtual_host",
    ("POST", "/api/hosts/virtual/delete"): "delete_virtual_host",
    ("GET", "/api/connector-types"): "get_connector_types",
    ("POST", "/api/connectors"): "post_connector",
    ("POST", "/api/connectors/delete"): "delete_connector",
    ("POST", "/api/connectors/test"): "post_connector_test",
    ("POST", "/api/connectors/devices"): "post_connector_devices",
    ("POST", "/api/devices/set"): "post_device_set",
    ("POST", "/api/bindings"): "post_bindings",
    ("POST", "/api/bindings/auto-match"): "post_auto_match",
    ("POST", "/api/bindings/release"): "post_binding_release",
    ("GET", "/api/devices/all"): "get_devices_all",
    ("POST", "/api/bindings/add"): "post_binding_add",
    ("POST", "/api/bindings/add-many"): "post_bindings_add_many",
    ("POST", "/api/bindings/update"): "post_binding_update",
    ("POST", "/api/bindings/delete"): "post_binding_delete",
    ("POST", "/api/engine"): "post_engine",
    ("POST", "/api/selftest"): "post_selftest",
    ("GET", "/api/logs"): "get_logs",
    ("POST", "/api/logs/open"): "post_open_logs",
    ("POST", "/api/open-url"): "post_open_url",
}


class _HTTPServer(ThreadingHTTPServer):
    # На Windows SO_REUSEADDR позволяет занять уже занятый порт — отключаем
    allow_reuse_address = sys.platform != "win32"
    daemon_threads = True


class Server:
    def __init__(self, app):
        self.app = app
        self.api = Api(app)
        self.httpd: ThreadingHTTPServer | None = None
        self.port = 0
        self.session_secret = pysecrets.token_hex(16)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/"

    def start(self) -> None:
        gen = self.app.config.get("general")
        lan = bool(gen.get("allow_lan"))
        bind = "0.0.0.0" if lan else "127.0.0.1"
        base = int(gen.get("web_port") or 8765)
        handler = self._handler_class()
        last_err = None
        for port in list(range(base, base + 20)) + [0]:
            try:
                self.httpd = _HTTPServer((bind, port), handler)
                break
            except OSError as e:
                last_err = e
        if not self.httpd:
            raise RuntimeError(f"не удалось запустить веб-сервер: {last_err}")
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        (paths.data_dir() / "port.txt").write_text(str(self.port))
        threading.Thread(target=self.httpd.serve_forever, name="web", daemon=True).start()
        journal.info(f"Панель управления: {self.url}" + (" (доступ из локальной сети включён)" if lan else ""), "system")

    def stop(self) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()

    def _handler_class(self):
        server = self
        static_dir = paths.resource_dir() / "static"

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"
            server_version = f"{APP_NAME}/{__version__}"

            def log_message(self, fmt, *args):  # без спама в консоль
                pass

            # ---- helpers
            def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8", extra: dict | None = None):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("X-Frame-Options", "DENY")
                for k, v in (extra or {}).items():
                    self.send_header(k, v)
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)

            def _json(self, code: int, obj, extra: dict | None = None):
                self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"), extra=extra)

            def _is_local_client(self) -> bool:
                return self.client_address[0] in ("127.0.0.1", "::1")

            def _host_ok(self) -> bool:
                if server.app.config.get("general", "allow_lan"):
                    return True
                host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip().lower()
                return host in LOCAL_HOSTS

            def _authorized(self) -> bool:
                if self._is_local_client():
                    return True
                pin = server.app.config.get("general", "lan_pin", "")
                if not pin:
                    return False
                c = cookies.SimpleCookie(self.headers.get("Cookie", ""))
                tok = c.get("ssb_auth")
                return bool(tok and hmac.compare_digest(tok.value, server.session_secret))

            def _body(self) -> dict:
                n = int(self.headers.get("Content-Length") or 0)
                if n <= 0:
                    return {}
                if n > 2_000_000:
                    raise BridgeError("слишком большой запрос")
                return json.loads(self.rfile.read(n).decode("utf-8") or "{}")

            # ---- methods
            def do_HEAD(self):
                self.do_GET()

            def do_GET(self):
                self._dispatch("GET")

            def do_POST(self):
                self._dispatch("POST")

            def _dispatch(self, method: str):
                try:
                    if not self._host_ok():
                        return self._send(403, b"Forbidden", "text/plain")
                    url = urlparse(self.path)
                    path = url.path
                    if path == "/api/login" and method == "POST":
                        return self._login()
                    if not path.startswith("/api/"):
                        return self._static(path)
                    if not self._authorized():
                        return self._json(401, {"error": "Требуется PIN-код", "need_pin": True})
                    if method == "POST" and self.headers.get("X-SSB") != "1":
                        return self._json(403, {"error": "forbidden"})
                    if path == "/api/open-url" and not self._is_local_client():
                        # с телефона/другого ПК ссылка откроется на их устройстве
                        return self._json(403, {"error": "только для локального окна"})
                    name = ROUTES.get((method, path))
                    if not name:
                        return self._json(404, {"error": "not found"})
                    q = {k: v[0] for k, v in parse_qs(url.query).items()}
                    body = self._body() if method == "POST" else {}
                    result = getattr(server.api, name)(q, body)
                    self._json(200, result)
                except (BridgeError, ValueError, KeyError) as e:
                    self._json(400, {"error": describe(e) if not isinstance(e, KeyError) else f"нет поля {e}"})
                except Exception as e:
                    journal.error(f"Ошибка панели ({self.path}): {describe(e)}", "system", exc=True)
                    self._json(500, {"error": describe(e)})

            def _login(self):
                body = self._body()
                pin = server.app.config.get("general", "lan_pin", "")
                if pin and pin != MASK and hmac.compare_digest(str(body.get("pin", "")), pin):
                    return self._json(200, {"ok": True}, {"Set-Cookie": f"ssb_auth={server.session_secret}; HttpOnly; SameSite=Strict; Path=/"})
                time.sleep(1)
                journal.warning(f"Неверный PIN-код с адреса {self.client_address[0]}", "system")
                return self._json(401, {"error": "Неверный PIN-код"})

            def _static(self, path: str):
                if path in ("", "/"):
                    path = "/index.html"
                target = (static_dir / path.lstrip("/")).resolve()
                if static_dir.resolve() not in target.parents or not target.is_file():
                    target = static_dir / "index.html"
                ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
                if ctype.startswith("text/") or ctype in ("application/javascript",):
                    ctype += "; charset=utf-8"
                self._send(200, target.read_bytes(), ctype)

        return Handler
