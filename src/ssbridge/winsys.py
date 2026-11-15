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
    k = ctypes.windll.kernel32
    if _mutex:
        k.CloseHandle(_mutex)  # повторная проверка (например, ожидание выхода другой копии)
    _mutex = k.CreateMutexW(None, False, f"Local\\{APP_ID}_{tag}")
    return k.GetLastError() != 183  # ERROR_ALREADY_EXISTS


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


def _prepare_profile(profile: Path) -> None:
    """Отключить в профиле окна панели менеджер паролей и автозаполнение."""
    import json
    # Профиль, в который Edge уже успел войти под учётной записью, сбрасываем
    # (в нём только служебные данные окна панели — настройки программы не здесь).
    try:
        state = json.loads((profile / "Local State").read_text(encoding="utf-8"))
        if any(v.get("user_name") or v.get("gaia_id") for v in state.get("profile", {}).get("info_cache", {}).values()):
            shutil.rmtree(profile, ignore_errors=True)
    except (OSError, ValueError, AttributeError):
        pass
    prefs_file = profile / "Default" / "Preferences"
    try:
        prefs = json.loads(prefs_file.read_text(encoding="utf-8")) if prefs_file.exists() else {}
    except (OSError, ValueError):
        prefs = {}
    # без входа в учётную запись Microsoft/Google и синхронизации
    # (иначе Edge сам входит под пользователем Windows и показывает окно «Данные синхронизируются»)
    prefs.setdefault("signin", {}).update({"allowed": False, "allowed_on_next_startup": False})
    prefs.setdefault("sync", {})["requested"] = False
    prefs.setdefault("browser", {}).update({"has_seen_welcome_page": True, "show_home_button": False})
    prefs["credentials_enable_service"] = False
    prefs["credentials_enable_autosignin"] = False
    prefs.setdefault("profile", {})["password_manager_enabled"] = False
    prefs.setdefault("autofill", {}).update({"enabled": False, "profile_enabled": False, "credit_card_enabled": False})
    prefs.setdefault("translate", {})["enabled"] = False
    try:
        prefs_file.parent.mkdir(parents=True, exist_ok=True)
        prefs_file.write_text(json.dumps(prefs), encoding="utf-8")
    except OSError:
        pass


PANEL_FLAGS = [
    "--no-first-run", "--no-default-browser-check", "--disable-sync", "--disable-save-password-bubble",
    "--disable-features=Translate,PasswordManagerOnboarding,AutofillServerCommunication,"
    "msImplicitSignin,msEdgeSyncConsentFRE,msSignInPromo,msUndersideButton,msHubApps,msEdgeSidebar,"
    "msShoppingTrigger,msWelcomePage,msEdgeAutoSignInFromOS",
]


def open_panel(url: str) -> None:
    """Открыть панель отдельным окном-приложением (Edge/Chrome) или в браузере."""
    browser = _find_browser()
    if browser:
        try:
            profile = paths.data_dir() / "ui-profile"
            _prepare_profile(profile)
            subprocess.Popen([browser, f"--app={url}", f"--user-data-dir={profile}", "--window-size=1280,860"] + PANEL_FLAGS,
                             close_fds=True)
            return
        except OSError:
            pass
    webbrowser.open(url)


def find_panel_windows() -> list[int]:
    """Открытые окна панели (окно-приложение Edge/Chrome с заголовком программы)."""
    if sys.platform != "win32":
        return []
    import ctypes
    from ctypes import wintypes
    u = ctypes.windll.user32
    found: list[int] = []
    want = paths.panel_title()
    proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        if not u.IsWindowVisible(hwnd):
            return True
        cls = ctypes.create_unicode_buffer(64)
        u.GetClassNameW(hwnd, cls, 64)
        if cls.value != "Chrome_WidgetWin_1":
            return True
        title = ctypes.create_unicode_buffer(256)
        u.GetWindowTextW(hwnd, title, 256)
        if title.value == want:
            found.append(int(hwnd))
        return True

    u.EnumWindows(proc(cb), 0)
    return found


def focus_window(hwnd: int) -> bool:
    """Развернуть (если свёрнуто) и вывести окно на передний план."""
    if sys.platform != "win32":
        return False
    import ctypes
    u = ctypes.windll.user32
    if not u.IsWindow(hwnd):
        return False
    if u.IsIconic(hwnd):
        u.ShowWindow(hwnd, 9)  # SW_RESTORE
    else:
        u.ShowWindow(hwnd, 5)  # SW_SHOW
    if u.SetForegroundWindow(hwnd) and u.GetForegroundWindow() == hwnd:
        return True
    # Windows разрешает перехват фокуса только «активному» процессу:
    # подключаемся к очереди ввода текущего активного окна и жмём Alt.
    k = ctypes.windll.kernel32
    fg = u.GetForegroundWindow()
    fg_thread = u.GetWindowThreadProcessId(fg, None) if fg else 0
    me = k.GetCurrentThreadId()
    attached = bool(fg_thread and fg_thread != me and u.AttachThreadInput(me, fg_thread, True))
    try:
        u.keybd_event(0x12, 0, 0, 0)
        u.keybd_event(0x12, 0, 2, 0)
        u.BringWindowToTop(hwnd)
        u.SetForegroundWindow(hwnd)
        u.SetActiveWindow(hwnd)
    finally:
        if attached:
            u.AttachThreadInput(me, fg_thread, False)
    return u.GetForegroundWindow() == hwnd


def close_panel_windows() -> int:
    """Закрыть все окна панели. Возвращает их количество."""
    if sys.platform != "win32":
        return 0
    import ctypes
    wins = find_panel_windows()
    for h in wins:
        ctypes.windll.user32.PostMessageW(h, 0x0010, 0, 0)  # WM_CLOSE
    return len(wins)


def message_box(text: str, title: str) -> None:
    if sys.platform == "win32" and not os.environ.get("SSBRIDGE_NO_MSGBOX"):
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, title, 0x40)  # MB_ICONINFORMATION


def allow_foreground() -> None:
    """Разрешить другому процессу (первой копии) вывести окно на передний план."""
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.AllowSetForegroundWindow(-1)  # ASFW_ANY


def open_url(url: str) -> None:
    """Открыть ссылку в браузере по умолчанию (только http/https)."""
    from urllib.parse import urlparse
    if urlparse(url).scheme not in ("http", "https"):
        raise ValueError("можно открывать только ссылки http/https")
    if sys.platform == "win32":
        os.startfile(url)  # noqa: S606 — браузер, назначенный в Windows по умолчанию
    else:
        webbrowser.open(url)


def open_folder(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(str(path))  # noqa: S606
    else:
        webbrowser.open(path.as_uri())
