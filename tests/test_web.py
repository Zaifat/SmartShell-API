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
