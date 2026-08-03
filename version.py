"""应用版本的唯一读取入口。"""

import sys
from pathlib import Path


def application_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def get_version() -> str:
    return (application_root() / "VERSION").read_text(encoding="utf-8").strip()


__version__ = get_version()
