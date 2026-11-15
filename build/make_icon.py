"""Генерация build/app.ico из того же рисунка, что и значок в трее."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ssbridge.tray import make_icon  # noqa: E402

out = ROOT / "build" / "app.ico"
img = make_icon(level="", size=256)
img.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(out)
