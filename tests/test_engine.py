import time

import pytest

from ssbridge.connectors.base import Connector, Device
from ssbridge.engine import Engine
from ssbridge.net import BridgeError, RateLimiter
from ssbridge.smartshell import Host


class FakeSS:
    def __init__(self, *a, **k):
        self.configured = True
        self.limiter = RateLimiter(15)
        self.hosts_list = []
        self.fail = False
        self.keepalives = []

    def hosts(self):
        if self.fail:
            raise BridgeError("нет сети")
        return list(self.hosts_list), [{"id": 1, "title": "Консоли"}]

    def host_keepalive(self, token):
        self.keepalives.append(token)

    def invalidate(self):
        pass

    def ensure_token(self):
        return "t"


class FakeConn(Connector):
    type_id = "fake"
    title = "Fake"

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.states = {"d1": False}
        self.commands = []
        self.fail = False
        self.stuck = False  # устройство «не слушается»

    def list_devices(self):
        if self.fail:
            raise BridgeError("offline")
        return [Device(id=k, name=k, state=v) for k, v in self.states.items()]

    def set_state(self, device_id, on):
        if self.fail:
            raise BridgeError("offline")
        self.commands.append((device_id, on))
        if not self.stuck:
            self.states[device_id] = on


def host(active=False, in_service=False, hid=10, alias="PS5-1"):
    return Host(id=hid, alias=alias, group_id=1, group="Консоли", active=active, in_service=in_service, online=True)


@pytest.fixture
def setup(tmp_config):
    ss = FakeSS()
    conn = FakeConn("c1", "Fake", {})
    tmp_config.upsert_club({"login": "l", "password": "p", "company_id": "1", "name": "Клуб"})
    tmp_config.update("connectors", [{"id": "c1", "type": "fake", "name": "Fake", "enabled": True, "settings": {}}])
    tmp_config.set_bindings([{"id": "b1", "host_id": 10, "host_alias": "PS5-1", "connector_id": "c1", "device_id": "d1",
                              "device_name": "d1", "enabled": True, "off_delay": 0}])
    eng = Engine(tmp_config, None, smartshell_factory=lambda *a, **k: ss, connector_factory=lambda conf: conn)
    return eng, ss, conn, tmp_config


def test_session_turns_device_on_and_off(setup):
    eng, ss, conn, _ = setup
    ss.hosts_list = [host(active=False)]
    eng.run_cycle()
    assert conn.commands == []  # уже выключено
    ss.hosts_list = [host(active=True)]
    eng.run_cycle()
    assert conn.commands == [("d1", True)]
    eng.run_cycle()
    assert conn.commands == [("d1", True)]  # без повторов
    ss.hosts_list = [host(active=False)]
    eng.run_cycle()
    assert conn.commands[-1] == ("d1", False)
    assert eng.overall()[0] == "ok"


def test_smartshell_down_holds_state(setup):
    eng, ss, conn, _ = setup
    ss.hosts_list = [host(active=True)]
    eng.run_cycle()
    ss.fail = True
    eng.run_cycle()
    eng.run_cycle()
    assert conn.commands == [("d1", True)]  # ничего не выключили
    assert eng.overall()[0] == "error"
    ss.fail = False
    eng.run_cycle()
    assert eng.club().ok is True


def test_off_delay(setup):
    eng, ss, conn, cfg = setup
    b = cfg.bindings()[0]
    b["off_delay"] = 2
    cfg.set_bindings([b])
    ss.hosts_list = [host(active=True)]
    eng.run_cycle()
    ss.hosts_list = [host(active=False)]
    eng.run_cycle()
    assert conn.commands == [("d1", True)]
    assert eng.bstate["b1"].off_since is not None
    time.sleep(2.1)
    eng.run_cycle()
    assert conn.commands[-1] == ("d1", False)


def test_session_resumes_during_delay(setup):
    eng, ss, conn, cfg = setup
    b = cfg.bindings()[0]
    b["off_delay"] = 60
    cfg.set_bindings([b])
    ss.hosts_list = [host(active=True)]
    eng.run_cycle()
    ss.hosts_list = [host(active=False)]
    eng.run_cycle()
    ss.hosts_list = [host(active=True)]
    eng.run_cycle()
    assert conn.commands == [("d1", True)]
    assert eng.bstate["b1"].off_since is None


def test_enforce_reverts_manual_change(setup):
    eng, ss, conn, _ = setup
    ss.hosts_list = [host(active=True)]
    eng.run_cycle()
    eng.run_cycle()  # подтверждение: устройство включилось
    conn.states["d1"] = False  # кто-то выключил розетку
    eng.bstate["b1"].last_cmd_ts -= 30  # прошло время после команды
    eng.run_cycle()
    assert conn.commands == [("d1", True), ("d1", True)]


def test_enforce_disabled(setup):
    eng, ss, conn, cfg = setup
    cfg.update("general", {"enforce_state": False})
    ss.hosts_list = [host(active=True)]
    eng.run_cycle()
    conn.states["d1"] = False
    eng.run_cycle()
    assert conn.commands == [("d1", True)]


def test_stuck_device_backoff(setup):
    eng, ss, conn, _ = setup
    conn.stuck = True
    ss.hosts_list = [host(active=True)]
    eng.run_cycle()
    eng.run_cycle()
    eng.run_cycle()
    assert len(conn.commands) == 1  # повтор только после паузы, без спама


def test_connector_failure_circuit_breaker(setup):
    eng, ss, conn, _ = setup
    ss.hosts_list = [host(active=True)]
    conn.fail = True
    eng.run_cycle()
    st = eng.cstate["c1"]
    assert st.ok is False and st.retry_at > time.time()
    assert eng.overall()[0] == "error"
    conn.fail = False
    eng.run_cycle()  # ещё на паузе
    assert conn.commands == []
    st.retry_at = 0
    eng.run_cycle()
    assert conn.commands == [("d1", True)]
    assert st.ok is True


def test_dry_run(setup):
    eng, ss, conn, cfg = setup
    cfg.update("general", {"dry_run": True})
    ss.hosts_list = [host(active=True)]
    eng.run_cycle()
    assert conn.commands == []


def test_service_mode_and_invert(setup):
    eng, ss, conn, cfg = setup
    b = cfg.bindings()[0]
    b["on_in_service"] = True
    cfg.set_bindings([b])
    ss.hosts_list = [host(active=False, in_service=True)]
    eng.run_cycle()
    assert conn.commands == [("d1", True)]
    b["on_in_service"] = False
    b["invert"] = True
    cfg.set_bindings([b])
    ss.hosts_list = [host(active=True)]
    eng.run_cycle()
    assert conn.commands[-1] == ("d1", False)


def test_host_resolved_by_alias(setup):
    eng, ss, conn, cfg = setup
    b = cfg.bindings()[0]
    b["host_id"] = None
    cfg.set_bindings([b])
    ss.hosts_list = [host(active=True, hid=77, alias="ps5-1")]
    eng.run_cycle()
    assert conn.commands == [("d1", True)]


def test_missing_host_warns(setup):
    eng, ss, conn, _ = setup
    ss.hosts_list = [host(hid=99, alias="other")]
    eng.run_cycle()
    assert eng.bstate["b1"].error
    assert eng.overall()[0] == "warn"


def test_manual_command_holds_auto(setup):
    eng, ss, conn, cfg = setup
    ss.hosts_list = [host(active=False)]
    eng.run_cycle()
    eng.command(cfg.bindings()[0], True, manual=True)
    eng.run_cycle()
    assert conn.commands == [("d1", True)]  # авто не выключило сразу
    assert eng.bstate["b1"].hold_until > time.time()


def test_virtual_host_keepalive(setup):
    eng, ss, conn, cfg = setup
    cfg.add_virtual_host(10, "PS5-1", "host-token")
    ss.hosts_list = [host()]
    eng.run_cycle()
    assert ss.keepalives == ["host-token"]
    eng.run_cycle()
    assert ss.keepalives == ["host-token"]  # не чаще интервала


def test_self_test_runs(setup, monkeypatch):
    eng, ss, conn, _ = setup
    import socket
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: type("S", (), {"close": lambda self: None})())
    ss.hosts_list = [host()]
    checks = eng.self_test()
    assert all(c["ok"] for c in checks), checks


def test_rate_limiter():
    rl = RateLimiter(3, period=0.5)
    assert all(rl.acquire(0) for _ in range(3))
    assert rl.acquire(0) is False
    time.sleep(0.55)
    assert rl.acquire(0)


def test_two_clubs_are_independent(tmp_config):
    """Сбой одного клуба не мешает переключать устройства другого."""
    ss_a, ss_b = FakeSS(), FakeSS()
    conn = FakeConn("c1", "Fake", {})
    conn.states = {"d1": False, "d2": False}
    a = tmp_config.upsert_club({"login": "a", "password": "p", "company_id": "1", "name": "Центр"})
    b = tmp_config.upsert_club({"login": "b", "password": "p", "company_id": "2", "name": "Север"})
    tmp_config.update("connectors", [{"id": "c1", "type": "fake", "name": "Fake", "enabled": True, "settings": {}}])
    tmp_config.set_bindings([
        {"id": "ba", "club_id": a["id"], "host_id": 10, "host_alias": "PC-1", "connector_id": "c1", "device_id": "d1"},
        {"id": "bb", "club_id": b["id"], "host_id": 10, "host_alias": "PC-1", "connector_id": "c1", "device_id": "d2"},
    ])
    by_company = {"1": ss_a, "2": ss_b}
    eng = Engine(tmp_config, None, smartshell_factory=lambda login, pw, cid, *a, **k: by_company[cid],
                 connector_factory=lambda conf: conn)
    ss_a.hosts_list = [host(active=True, alias="PC-1")]
    ss_b.hosts_list = [host(active=False, alias="PC-1")]
    eng.run_cycle()
    assert conn.commands == [("d1", True)]  # хост 10 активен только в клубе «Центр»
    st = eng.status()
    assert [c["name"] for c in st["clubs"]] == ["Центр", "Север"]
    assert {x["id"]: x["club_name"] for x in st["bindings"]} == {"ba": "Центр", "bb": "Север"}
    # «Центр» недоступен: его устройство удерживается, «Север» работает
    ss_a.fail = True
    ss_b.hosts_list = [host(active=True, alias="PC-1")]
    eng.run_cycle()
    assert conn.commands == [("d1", True), ("d2", True)]
    level, text = eng.overall()
    assert level == "error" and "Центр" in text
    ss_a.hosts_list = [host(active=False, alias="PC-1")]
    eng.run_cycle()
    assert conn.commands == [("d1", True), ("d2", True)]  # пока нет связи — ничего не выключаем
    ss_a.fail = False
    eng.run_cycle()
    assert conn.commands[-1] == ("d1", False)
    assert eng.overall()[0] == "ok"


def test_disabled_club_binding_reports_error(setup):
    eng, ss, conn, cfg = setup
    kid = cfg.clubs()[0]["id"]
    cfg.upsert_club({"id": kid, "enabled": False})
    eng.run_cycle()
    assert eng.status()["bindings"][0]["state"]["error"] == "клуб SmartShell удалён или отключён"
    assert eng.overall()[0] == "setup" or eng.overall()[0] in ("warn", "error")
