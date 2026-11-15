import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("SSBRIDGE_DATA", tempfile.mkdtemp(prefix="ssbridge-test-"))

import pytest  # noqa: E402

from ssbridge import journal  # noqa: E402

journal.setup(to_file=False)


@pytest.fixture
def tmp_config(tmp_path):
    from ssbridge.config import Config
    return Config(tmp_path / "config.json")
