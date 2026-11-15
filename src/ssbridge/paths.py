"""Расположение файлов программы.

Все данные хранятся в %APPDATA%\\SmartShellBridge. Если рядом с exe лежит
файл ``portable.txt`` — данные хранятся в папке ``data`` рядом с exe
(портативный режим, удобно для флешки или переноса).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from . import APP_ID, APP_NAME


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def exe_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def resource_dir() -> Path:
    """Папка со встроенными ресурсами (static, иконки)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / "ssbridge"
    return Path(__file__).resolve().parent


def data_dir() -> Path:
    override = os.environ.get("SSBRIDGE_DATA")
    if override:
        p = Path(override)
    elif (exe_dir() / "portable.txt").exists():
        p = exe_dir() / "data"
    else:
        root = os.environ.get("APPDATA") or str(Path.home())
        p = Path(root) / APP_ID
    p.mkdir(parents=True, exist_ok=True)
    return p


def logs_dir() -> Path:
    p = data_dir() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def config_path() -> Path:
    return data_dir() / "config.json"


def panel_title() -> str:
    """Заголовок окна панели. У портативных/тестовых копий он свой —
    так окна разных копий программы не путаются между собой."""
    if os.environ.get("SSBRIDGE_DATA"):
        return f"{APP_NAME} [{Path(os.environ['SSBRIDGE_DATA']).name}]"
    if (exe_dir() / "portable.txt").exists():
        return f"{APP_NAME} [портативная, {exe_dir().name}]"
    return APP_NAME
