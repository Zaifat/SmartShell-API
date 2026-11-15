"""Значок в системном трее (цвет показывает состояние)."""
from __future__ import annotations

import threading

from PIL import Image, ImageDraw

from . import APP_NAME, paths, winsys

COLORS = {"ok": (34, 197, 94), "warn": (245, 158, 11), "error": (239, 68, 68), "paused": (148, 163, 184), "setup": (59, 130, 246)}


def make_icon(level: str = "ok", size: int = 64) -> Image.Image:
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # фон — скруглённый квадрат с градиентом
    grad = Image.new("RGBA", (s, s))
    gd = ImageDraw.Draw(grad)
    for y in range(s):
        t = y / s
        gd.line([(0, y), (s, y)], fill=(int(99 + (139 - 99) * t), int(102 + (92 - 102) * t), int(241 + (246 - 241) * t), 255))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.24), fill=255)
    img.paste(grad, (0, 0), mask)
    # молния
    k = s / 64
    bolt = [(36, 8), (16, 36), (30, 36), (26, 56), (48, 26), (34, 26), (38, 8)]
    d.polygon([(x * k, y * k) for x, y in bolt], fill=(255, 255, 255, 255))
    # индикатор состояния
    if level:
        r = int(s * 0.2)
        cx, cy = s - r - 1, s - r - 1
        d.ellipse([cx - r - 2 * k, cy - r - 2 * k, cx + r + 2 * k, cy + r + 2 * k], fill=(15, 23, 42, 255))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=COLORS.get(level, COLORS["ok"]) + (255,))
    return img


class Tray:
    def __init__(self, app):
        self.app = app
        self.icon = None
        self._level = None

    def run(self) -> None:
        """Блокирующий запуск (в главном потоке)."""
        import pystray
        from pystray import Menu, MenuItem as Item

        def autostart_checked(_):
            return winsys.autostart_enabled()

        def toggle_autostart(icon, item):
            winsys.set_autostart(not winsys.autostart_enabled())
            self.app.config.update("general", {"autostart": winsys.autostart_enabled()})

        def paused_checked(_):
            return self.app.engine.paused

        menu = Menu(
            Item("Открыть панель управления", lambda: self.app.open_panel(), default=True),
            Menu.SEPARATOR,
            Item(lambda _: self.app.engine.overall()[1], None, enabled=False),
            Item("Синхронизировать сейчас", lambda: self.app.engine.run_now()),
            Item("Пауза синхронизации", lambda: self.app.engine.set_paused(not self.app.engine.paused), checked=paused_checked),
            Menu.SEPARATOR,
            Item("Открыть папку журналов", lambda: winsys.open_folder(paths.logs_dir())),
            Item("Запускать вместе с Windows", toggle_autostart, checked=autostart_checked),
            Menu.SEPARATOR,
            Item("Выход", lambda: self.app.quit()),
        )
        self.icon = pystray.Icon("ssbridge", make_icon("setup"), APP_NAME, menu)
        self.app.engine.add_listener(self.refresh)
        threading.Timer(1.0, self.refresh).start()
        self.icon.run()

    def refresh(self) -> None:
        if not self.icon:
            return
        level, text = self.app.engine.overall()
        try:
            if level != self._level:
                self.icon.icon = make_icon(level)
                self._level = level
            self.icon.title = f"{APP_NAME}\n{text}"[:127]
            self.icon.update_menu()
        except Exception:
            pass

    def notify(self, text: str) -> None:
        try:
            if self.icon and getattr(self.icon, "HAS_NOTIFICATION", True):
                self.icon.notify(text, APP_NAME)
        except Exception:
            pass

    def stop(self) -> None:
        if self.icon:
            self.icon.stop()
