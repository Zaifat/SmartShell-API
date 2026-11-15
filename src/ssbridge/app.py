"""Точка входа: запуск движка, веб-панели и значка в трее."""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
import urllib.request

from . import APP_NAME, __version__, journal, paths, winsys
from .config import Config
from .engine import Engine
from .notify import Notifier


class App:
    def __init__(self, args):
        self.args = args
        self.config = Config()
        self.notifier = Notifier(lambda: self.config.get("notify"))
        self.engine = Engine(self.config, self.notifier)
        from .web import Server
        self.server = Server(self)
        self.tray = None
        self._quit = threading.Event()

    def open_panel(self) -> None:
        winsys.open_panel(self.server.url)

    def run(self) -> None:
        journal.info(f"{APP_NAME} {__version__} запущен. Папка данных: {paths.data_dir()}", "system")
        if self.config.load_error:
            journal.warning(self.config.load_error, "config")
        # Автозапуск прописывается только если пользователь сам его включил
        # (и обновляется путь, если exe перенесли в другую папку).
        try:
            if self.config.get("general", "autostart", False) and not winsys.autostart_current():
                winsys.set_autostart(True)
        except Exception as e:
            journal.warning(f"Не удалось настроить автозапуск: {e}", "system")

        self.server.start()
        self.engine.start()

        first_run = not self.config.get("wizard_done")
        if not self.args.no_browser and (not self.args.minimized or first_run):
            threading.Timer(0.5, self.open_panel).start()

        if self.args.no_tray:
            try:
                while not self._quit.is_set():
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            self.shutdown()
            return
        from .tray import Tray
        self.tray = Tray(self)
        try:
            self.tray.run()  # блокирует до выхода
        except Exception as e:
            journal.error(f"Значок в трее недоступен ({e}), программа продолжает работу в фоне", "system")
            self._quit.wait()
        self.shutdown()

    def quit(self) -> None:
        self._quit.set()
        if self.tray:
            self.tray.stop()

    def shutdown(self) -> None:
        journal.info("Программа завершает работу", "system")
        self.engine.stop()
        self.server.stop()


def _excepthook(exc_type, exc, tb):
    import traceback
    journal.error("Критическая ошибка: " + "".join(traceback.format_exception(exc_type, exc, tb))[-2000:], "system")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="SmartShellBridge", description=f"{APP_NAME} {__version__}")
    parser.add_argument("--minimized", action="store_true", help="запуск свёрнутым в трей")
    parser.add_argument("--no-tray", action="store_true", help="без значка в трее (консольный режим)")
    parser.add_argument("--no-browser", action="store_true", help="не открывать окно панели при запуске")
    parser.add_argument("--debug", action="store_true", help="подробный журнал")
    parser.add_argument("--selftest", action="store_true", help="выполнить диагностику и выйти")
    args = parser.parse_args(argv)

    # pythonw / windowed exe: stdout отсутствует
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    journal.setup(debug=args.debug)
    sys.excepthook = _excepthook
    threading.excepthook = lambda a: _excepthook(a.exc_type, a.exc_value, a.exc_traceback)

    if args.selftest:
        cfg = Config()
        eng = Engine(cfg)
        ok = True
        for c in eng.self_test():
            ok &= c["ok"]
            print(("[OK]   " if c["ok"] else "[FAIL] ") + f"{c['name']}: {c['message']}")
        return 0 if ok else 1

    if not winsys.acquire_single_instance():
        # уже запущено — просто открываем панель существующего экземпляра
        try:
            port = (paths.data_dir() / "port.txt").read_text().strip()
            url = f"http://127.0.0.1:{port}/"
            urllib.request.urlopen(url + "api/state", timeout=3)
            winsys.open_panel(url)
        except Exception:
            pass
        return 0

    App(args).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
