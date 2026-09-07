import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(getattr(sys, '_MEIPASS'))
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

ASSETS_DIR = BASE_DIR / "assets"

ICON_PATH = ASSETS_DIR / "icon.ico"
SVG_PATH = ASSETS_DIR / "icon.svg"
PNG_PATH = ASSETS_DIR / "icon_256.png"

MAX_POSITIVE_INTEGER = 2147483647
