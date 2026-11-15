"""Демо-стенд для ручной проверки интерфейса без настоящего клуба.

Запуск:  python tests/demo_server.py [порт]
Поднимает панель с тестовым SmartShell (8 хостов, сеансы меняются сами)
и тестовой системой умного дома (розетки). Данные — во временной папке.
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

    def __init__(self, *a, **k):
        self.limiter = RateLimiter(15)
        self.groups = [{"id": 1, "title": "Игровые ПК"}, {"id": 2, "title": "Консоли"}]
        self.hosts_list = [Host(i, f"PC-{i:02d}", 1, "Игровые ПК", False, False, True) for i in range(1, 6)]
        self.hosts_list += [Host(101, "PS5-1", 2, "Консоли", False, False, True), Host(102, "ps5 2", 2, "Консоли", False, False, True),
                            Host(103, "XBOX-1", 2, "Консоли", True, False, True)]
        self.next_id = 200

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
        self.config.update("smartshell", {"login": "demo", "password": "demo", "company_id": "1", "club_name": "Демо-клуб"}, save=False)
        self.config.update("wizard_done", True, save=False)
        self.config.upsert_connector({"type": "demo", "name": "Демо-розетки", "enabled": True, "settings": {}})
        self.ss = DemoSS()
        self.engine = Engine(self.config, None, smartshell_factory=lambda *a, **k: self.ss)
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
