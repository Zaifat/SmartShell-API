"""Демо-стенд для ручной проверки интерфейса без настоящего клуба.

Запуск:  python tests/demo_server.py [порт]
Поднимает панель с двумя тестовыми клубами SmartShell (сеансы меняются сами)
и тестовой системой умного дома (розетки). Данные — во временной папке.
Поиск клубов по логину возвращает три клуба (третий ещё не добавлен).
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.environ["SSBRIDGE_DATA"] = tempfile.mkdtemp(prefix="ssbridge-demo-")

from ssbridge import journal  # noqa: E402
from ssbridge.config import Config  # noqa: E402
from ssbridge.connectors.base import Connector, Device, register  # noqa: E402
from ssbridge.engine import Engine  # noqa: E402
from ssbridge.net import RateLimiter  # noqa: E402
from ssbridge.smartshell import Host  # noqa: E402
from ssbridge.web import Server  # noqa: E402


@register
class DemoSockets(Connector):
    type_id = "demo"
    title = "Демо-розетки"
    description = "Тестовые устройства для проверки интерфейса"
    category = "local"
    fields = []
    STATES = {"PS5-1": False, "PS5-2": False, "XBOX-1": False, "Телевизор зал": False, "Руль симулятор": False, "Лампа VIP": True}

    def list_devices(self):
        time.sleep(0.3)
        return [Device(id=k, name=k, state=v, room="Консольная" if "PS" in k or "XBOX" in k else "Зал", kind="socket")
                for k, v in self.STATES.items()]

    def set_state(self, device_id, on):
        self.STATES[device_id] = on


class DemoSS:
    configured = True
    INSTANCES: dict = {}

    def __new__(cls, login="", password="", company_id="1", *a, **k):
        # один объект на клуб — состояние хостов сохраняется между пересозданиями
        cid = str(company_id or "1")
        if cid not in cls.INSTANCES:
            obj = super().__new__(cls)
            obj._init(cid)
            cls.INSTANCES[cid] = obj
        return cls.INSTANCES[cid]

    def __init__(self, *a, **k):
        pass

    def _init(self, cid):
        self.login_name, self.password = "demo", "demo"
        self.limiter = RateLimiter(15)
        self.groups = [{"id": 1, "title": "Игровые ПК"}, {"id": 2, "title": "Консоли"}]
        base = 1000 * (int(cid) if cid.isdigit() else 9)
        if cid == "1":
            self.hosts_list = [Host(i, f"PC-{i:02d}", 1, "Игровые ПК", False, False, True) for i in range(1, 6)]
            self.hosts_list += [Host(101, "PS5-1", 2, "Консоли", False, False, True), Host(102, "ps5 2", 2, "Консоли", False, False, True),
                                Host(103, "XBOX-1", 2, "Консоли", True, False, True)]
        else:
            self.hosts_list = [Host(base + i, f"ПК-{i}", 1, "Игровые ПК", i == 2, False, True) for i in range(1, 4)]
            self.hosts_list += [Host(base + 50, "VR-1", 2, "Консоли", False, False, True)]
        self.next_id = base + 200

    def clubs(self):
        return [{"id": 1, "name": "Демо-клуб", "address": "ул. Ленина, 1"},
                {"id": 2, "name": "Демо Север", "address": "пр. Мира, 15"},
                {"id": 3, "name": "Демо Юг", "address": "ул. Южная, 7"}]

    def authenticate(self):
        return "t"

    def hosts(self):
        return list(self.hosts_list), self.groups

    def register_host(self, alias, group_id):
        g = next(g for g in self.groups if g["id"] == group_id)
        self.next_id += 1
        self.hosts_list.append(Host(self.next_id, alias, group_id, g["title"], False, False, True))
        return f"token-{self.next_id}"

    def host_keepalive(self, token):
        pass

    def invalidate(self):
        pass

    def ensure_token(self):
        return "t"


class DemoNotifier:
    def enabled(self):
        return False

    def send_now(self, text):
        raise ValueError("демо")


class DemoApp:
    def __init__(self, port):
        self.config = Config()
        self.config.update("general", {"web_port": port, "autostart": False, "poll_interval": 5}, save=False)
        self.config.upsert_club({"login": "demo", "password": "demo", "company_id": "1", "name": "Демо-клуб"})
        self.config.upsert_club({"login": "demo", "password": "demo", "company_id": "2", "name": "Демо Север"})
        self.config.update("wizard_done", True, save=False)
        self.config.upsert_connector({"type": "demo", "name": "Демо-розетки", "enabled": True, "settings": {}})
        self.ss = DemoSS("demo", "demo", "1")
        self.engine = Engine(self.config, None, smartshell_factory=DemoSS)
        import ssbridge.web
        ssbridge.web.SmartShell = DemoSS  # поиск клубов и проверка входа без сети
        self.notifier = DemoNotifier()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18900
    journal.setup(to_file=False)
    app = DemoApp(port)
    srv = Server(app)
    srv.start()
    app.engine.start()

    def flip():  # сеансы на PS5-1 включаются/выключаются каждые 20 с
        while True:
            time.sleep(20)
            h = next(h for h in app.ss.hosts_list if h.id == 101)
            h.active = not h.active
    threading.Thread(target=flip, daemon=True).start()
    print(f"demo: {srv.url}", flush=True)
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
