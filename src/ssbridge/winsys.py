"""Интеграция с Windows: автозапуск, единственный экземпляр, окно панели."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

from . import APP_ID, paths

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _launch_command() -> str:
    if paths.is_frozen():
        return f'"{sys.executable}" --minimized'
    pyw = Path(sys.executable).with_name("pythonw.exe")
    exe = pyw if pyw.exists() else Path(sys.executable)
    return f'"{exe}" -m ssbridge --minimized'


def autostart_enabled() -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            val, _ = winreg.QueryValueEx(k, APP_ID)
            return bool(val)
    except OSError:
        return False


def autostart_current() -> bool:
    """Автозапуск включён и указывает на текущий exe."""
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            val, _ = winreg.QueryValueEx(k, APP_ID)
            return val == _launch_command()
    except OSError:
        return False


def set_autostart(enabled: bool) -> None:
    if sys.platform != "win32":
        return
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
        if enabled:
            winreg.SetValueEx(k, APP_ID, 0, winreg.REG_SZ, _launch_command())
        else:
            try:
                winreg.DeleteValue(k, APP_ID)
            except OSError:
                pass


_mutex = None


def acquire_single_instance() -> bool:
    """True, если это первый экземпляр программы."""
    global _mutex
    if sys.platform != "win32":
        return True
    import ctypes
    import hashlib
    # Один экземпляр на папку данных (портативные копии не мешают друг другу)
    tag = hashlib.sha1(str(paths.data_dir()).lower().encode()).hexdigest()[:12]
    _mutex = ctypes.windll.kernel32.CreateMutexW(None, False, f"Local\\{APP_ID}_{tag}")
    return ctypes.windll.kernel32.GetLastError() != 183  # ERROR_ALREADY_EXISTS


def _find_browser() -> str | None:
    candidates = []
    for env in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            candidates += [Path(base) / "Microsoft/Edge/Application/msedge.exe",
                           Path(base) / "Google/Chrome/Application/chrome.exe"]
    for c in candidates:
        if c.exists():
            return str(c)
    return shutil.which("msedge") or shutil.which("chrome")


def open_panel(url: str) -> None:
    """Открыть панель отдельным окном-приложением (Edge/Chrome) или в браузере."""
    browser = _find_browser()
    if browser:
        try:
            profile = paths.data_dir() / "ui-profile"
            subprocess.Popen([browser, f"--app={url}", f"--user-data-dir={profile}", "--window-size=1280,860",
                              "--no-first-run", "--no-default-browser-check", "--disable-features=Translate"], close_fds=True)
            return
        except OSError:
            pass
    webbrowser.open(url)


def open_folder(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(str(path))  # noqa: S606
    else:
        webbrowser.open(path.as_uri())
