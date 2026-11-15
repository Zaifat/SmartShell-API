# -*- mode: python ; coding: utf-8 -*-
# Сборка: pyinstaller build/SmartShellBridge.spec  (см. build.ps1)
from pathlib import Path

ROOT = Path(SPECPATH).parent
SRC = ROOT / "src"

a = Analysis(
    [str(SRC / "ssbridge" / "__main__.py")],
    pathex=[str(SRC)],
    datas=[(str(SRC / "ssbridge" / "static"), "ssbridge/static")],
    hiddenimports=["pystray._win32", "paho.mqtt.client"],
    excludes=["tkinter", "unittest", "pydoc", "test"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SmartShellBridge",
    icon=str(ROOT / "build" / "app.ico"),
    version=str(ROOT / "build" / "version_info.txt"),
    console=False,
    upx=False,
    runtime_tmpdir=None,
)
