import http.client
import json

import pytest

from ssbridge.engine import Engine
from ssbridge.web import Server, _norm


class FakeApp:
    def __init__(self, cfg):
        self.config = cfg
        self.engine = Engine(cfg)
        self.notifier = None


@pytest.fixture
def server(tmp_config):
    tmp_config.update("general", {"web_port": 18765})
    srv = Server(FakeApp(tmp_config))
    srv.start()
    yield srv
    srv.stop()


def req(srv, method, path, body=None, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", srv.port, timeout=10)
    h = {"Content-Type": "application/json", **(headers or {})}
    conn.request(method, path, body=json.dumps(body) if body is not None else None, headers=h)
    r = conn.getresponse()
    data = r.read()
    conn.close()
    return r.status, data


def test_static_and_state(server):
    st, body = req(server, "GET", "/")
    assert st == 200 and b"SmartShell Bridge" in body
    st, body = req(server, "GET", "/api/state")
    data = json.loads(body)
    assert st == 200 and data["level"] == "setup" and "version" in data


def test_post_requires_csrf_header(server):
    st, _ = req(server, "POST", "/api/engine", {"action": "pause"})
    assert st == 403
    st, body = req(server, "POST", "/api/engine", {"action": "pause"}, {"X-SSB": "1"})
    assert st == 200 and json.loads(body)["paused"] is True


def test_dns_rebinding_blocked(server):
    st, _ = req(server, "GET", "/api/state", headers={"Host": "evil.example.com"})
    assert st == 403


def test_config_masks_secrets(server, tmp_config):
    tmp_config.update("smartshell", {"login": "7900", "password": "topsecret"})
    st, body = req(server, "GET", "/api/config")
    assert b"topsecret" not in body
    data = json.loads(body)
    assert data["smartshell"]["login"] == "7900"


def test_connector_types_and_crud(server, tmp_config):
    st, body = req(server, "GET", "/api/connector-types")
    assert len(json.loads(body)["types"]) >= 12
    st, body = req(server, "POST", "/api/connectors", {"type": "webhook", "name": "Hooks", "settings": {"devices": []}}, {"X-SSB": "1"})
    assert st == 200
    cid = json.loads(body)["connector"]["id"]
    assert tmp_config.connector(cid)["name"] == "Hooks"
    st, body = req(server, "POST", "/api/connectors/delete", {"id": cid}, {"X-SSB": "1"})
    assert st == 200 and tmp_config.connector(cid) is None


def test_path_traversal(server):
    st, body = req(server, "GET", "/../../config.json")
    assert st == 200 and b"<!doctype html>" in body.lower()


def test_logs_endpoint(server):
    st, body = req(server, "GET", "/api/logs?after=0")
    assert st == 200 and "items" in json.loads(body)


def test_norm_matches_mixed_alphabets():
    assert _norm("PS5-1") == _norm("ps5 1")
    assert _norm("ХВОХ") == _norm("XBOX")  # кириллица vs латиница
    assert _norm("ПС4") != _norm("ПС5")


def test_open_url_only_http(server, monkeypatch):
    import os
    opened = []
    monkeypatch.setattr(os, "startfile", lambda u: opened.append(u), raising=False)
    st, _ = req(server, "POST", "/api/open-url", {"url": "https://smartshell.gg"}, {"X-SSB": "1"})
    assert st == 200 and opened == ["https://smartshell.gg"]
    st, _ = req(server, "POST", "/api/open-url", {"url": "file:///C:/Windows/system32/calc.exe"}, {"X-SSB": "1"})
    assert st == 400 and len(opened) == 1


# ---------------------------------------------------------------- хосты и привязки
from ssbridge.connectors.base import Connector, Device, register  # noqa: E402
from ssbridge.net import RateLimiter  # noqa: E402
from ssbridge.smartshell import Host  # noqa: E402


@register
class _TestSockets(Connector):
    type_id = "test_sockets"
    title = "Test"
    fields = []

    def list_devices(self):
        return [Device(id="d1", name="PS5-1", state=False), Device(id="d2", name="Xbox", state=True)]

    def set_state(self, device_id, on):
        pass


class _SS:
    configured = True

    def __init__(self):
        self.limiter = RateLimiter(15)
        self.hosts_list = [Host(10, "ps5 1", 1, "Консоли", False, False, True)]
        self.registered = []

    def hosts(self):
        return list(self.hosts_list), [{"id": 1, "title": "Консоли"}]

    def register_host(self, alias, group_id):
        self.registered.append((alias, group_id))
        self.hosts_list.append(Host(11, alias, group_id, "Консоли", False, False, True))
        return "host-token"

    def host_keepalive(self, token):
        pass


@pytest.fixture
def hserver(tmp_config):
    tmp_config.update("general", {"web_port": 18770})
    tmp_config.update("smartshell", {"login": "l", "password": "p", "company_id": "1"})
    conn = tmp_config.upsert_connector({"type": "test_sockets", "name": "Розетки", "settings": {}})
    app = FakeApp(tmp_config)
    ss = _SS()
    app.engine = Engine(tmp_config, smartshell_factory=lambda *a, **k: ss)
    srv = Server(app)
    srv.start()
    yield srv, tmp_config, conn["id"], ss
    srv.stop()


def post(srv, path, body):
    st, data = req(srv, "POST", path, body, {"X-SSB": "1"})
    return st, json.loads(data)


def test_devices_all(hserver):
    srv, cfg, cid, _ = hserver
    st, data = req(srv, "GET", "/api/devices/all")
    data = json.loads(data)
    assert st == 200 and data["systems"][0]["ok"] and len(data["systems"][0]["devices"]) == 2


def test_binding_add_update_delete(hserver):
    srv, cfg, cid, _ = hserver
    st, r = post(srv, "/api/bindings/add", {"host_id": 10, "host_alias": "ps5 1", "connector_id": cid, "device_id": "d1", "device_name": "PS5-1"})
    assert st == 200 and r["created"]
    bid = r["binding"]["id"]
    st, r2 = post(srv, "/api/bindings/add", {"host_id": 10, "host_alias": "ps5 1", "connector_id": cid, "device_id": "d1"})
    assert r2["created"] is False and len(cfg.bindings()) == 1  # без дубликатов
    st, r = post(srv, "/api/bindings/update", {"id": bid, "off_delay": 120, "on_in_service": True, "host_id": 999})
    assert st == 200 and r["binding"]["off_delay"] == 120 and r["binding"]["on_in_service"] is True
    assert cfg.bindings()[0]["host_id"] == 10  # посторонние поля не меняются
    st, r = post(srv, "/api/bindings/delete", {"id": bid})
    assert st == 200 and cfg.bindings() == []
    st, r = post(srv, "/api/bindings/delete", {"id": bid})
    assert st == 400 and "не найдена" in r["error"]


def test_binding_add_validation(hserver):
    srv, cfg, cid, _ = hserver
    st, r = post(srv, "/api/bindings/add", {"host_id": 10, "connector_id": "nope", "device_id": "d1"})
    assert st == 400
    st, r = post(srv, "/api/bindings/add", {"host_id": 10, "connector_id": cid})
    assert st == 400


def test_add_many(hserver):
    srv, cfg, cid, _ = hserver
    items = [{"host_id": 10, "host_alias": "ps5 1", "connector_id": cid, "device_id": "d1"},
             {"host_id": 10, "host_alias": "ps5 1", "connector_id": cid, "device_id": "d1"},
             {"host_id": 10, "connector_id": "bad", "device_id": "x"}]
    st, r = post(srv, "/api/bindings/add-many", {"items": items})
    assert r["added"] == 1


def test_auto_match_by_name(hserver):
    srv, cfg, cid, _ = hserver
    st, r = post(srv, "/api/bindings/auto-match", {})
    assert [(m["host_id"], m["device_id"]) for m in r["matches"]] == [(10, "d1")]


def test_console_host_created_and_bound(hserver):
    srv, cfg, cid, ss = hserver
    st, r = post(srv, "/api/hosts/virtual", {"alias": "Xbox", "group_id": 1, "connector_id": cid, "device_id": "d2", "device_name": "Xbox"})
    assert st == 200 and ss.registered == [("Xbox", 1)]
    assert r["binding"]["host_id"] == 11 and r["binding"]["device_id"] == "d2"
    assert cfg.virtual_hosts()[0]["host_id"] == 11
    st, r = post(srv, "/api/hosts/virtual", {"alias": "xbox"})
    assert st == 400 and "уже есть" in r["error"]


def test_hosts_endpoint(hserver):
    srv, cfg, cid, _ = hserver
    st, data = req(srv, "GET", "/api/hosts?refresh=1")
    data = json.loads(data)
    assert data["hosts"][0]["alias"] == "ps5 1" and data["groups"][0]["title"] == "Консоли"
