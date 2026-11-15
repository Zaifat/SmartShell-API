"""Точка входа: запуск движка, веб-панели и значка в трее."""
from __future__ import annotations

import argparse
import logging
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
        self._panel_lock = threading.Lock()
        self._panel_launched = -1e9

    def open_panel(self) -> None:
        """Показать окно панели: существующее — на передний план, иначе открыть одно новое."""
        with self._panel_lock:
            wins = winsys.find_panel_windows()
            if wins:
                winsys.focus_window(wins[0])
                return
            # окно запускается 1–3 с: повторные клики в это время не плодят копии
            if time.monotonic() - self._panel_launched < 8:
                return
            self._panel_launched = time.monotonic()
            winsys.open_panel(self.server.url)

    def run(self) -> None:
        journal.info(f"{APP_NAME} {__version__} запущен. Папка данных: {paths.data_dir()}", "system")
        if self.config.load_error:
            journal.warning(self.config.load_error, "config")
        # Автозапуск прописывается только если пользователь сам его включил
        # (и обновляется путь, если exe перенесли в другую папку).
        try:
            if winsys.autostart_enabled() and not self.config.get("general", "autostart", False):
                self.config.update("general", {"autostart": True})  # включён установщиком
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
        """Полный выход: закрыть окно панели, значок в трее и остановить программу."""
        if self._quit.is_set():
            return
        self._quit.set()
        # страховка: что бы ни зависло при остановке — процесс завершится
        t = threading.Timer(15, lambda: os._exit(0))
        t.daemon = True
        t.start()
        try:
            winsys.close_panel_windows()
        except Exception:
            pass
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
    parser.add_argument("--quit", action="store_true", help="закрыть уже запущенную программу (для установщика)")
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
        return _quit_running() if args.quit else _activate_running(args)
    if args.quit:
        return 0  # программа не запущена

    App(args).run()
    # не ждём фоновых потоков (сетевые запросы и т.п.) — программа закрывается сразу
    logging.shutdown()
    os._exit(0)


def _post_running(path: str, timeout: float = 5) -> None:
    port = (paths.data_dir() / "port.txt").read_text().strip()
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=b"{}", method="POST",
                                 headers={"X-SSB": "1", "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=timeout).read()


def _quit_running() -> int:
    """Попросить запущенную копию закрыться и дождаться этого (до 10 с)."""
    try:
        _post_running("/api/app/quit")
    except Exception:
        return 1
    for _ in range(40):
        time.sleep(0.25)
        if winsys.acquire_single_instance():
            return 0
    return 1


def _activate_running(args) -> int:
    """Программа уже запущена: показать её окно вместо запуска второй копии."""
    if args.minimized:
        return 0  # повторный автозапуск — ничего не делаем
    try:
        wins = winsys.find_panel_windows()
        if wins:
            winsys.focus_window(wins[0])
            return 0
        winsys.allow_foreground()
        _post_running("/api/app/show")
    except Exception as e:
        journal.warning(f"Не удалось показать окно уже запущенной программы: {e}", "system")
    return 0


if __name__ == "__main__":
    sys.exit(main())
