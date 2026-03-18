from __future__ import annotations

import os
from pathlib import Path
import sys


class Config:
    # Grid
    GRID_WIDTH = 24
    GRID_HEIGHT = 18
    TILE_SIZE = 32

    # Timing
    BASE_STEPS_PER_SECOND = 5.0
    SPEED_PER_FOOD = 0.35
    MAX_STEPS_PER_SECOND = 12.0
    TARGET_FPS = 60

    # Window
    WINDOW_TITLE = "星露谷风贪吃蛇"
    HUD_HEIGHT = 72
    FONT_NAME = "microsoftyaheiui"

    # Palette
    COLOR_BG = (162, 205, 140)
    COLOR_SOIL = (127, 90, 62)
    COLOR_BORDER = (88, 60, 42)
    COLOR_TEXT = (41, 39, 35)
    COLOR_ACCENT = (247, 222, 132)

    COLOR_SNAKE_HEAD = (78, 129, 79)
    COLOR_SNAKE_BODY = (98, 156, 97)
    COLOR_SNAKE_BELLY = (174, 207, 160)

    COLOR_FOOD_MAIN = (220, 92, 74)
    COLOR_FOOD_LEAF = (91, 154, 83)

    # Files
    HIGH_SCORE_FILE = "high_score.json"
    SETTINGS_FILE = "settings.json"
    SAVE_FILE = "savegame.json"
    APP_DIR_NAME = "stardew_snake"


def get_base_path() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent


def get_data_path() -> Path:
    candidates: list[Path] = []

    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        candidates.append(Path(local_appdata) / Config.APP_DIR_NAME)

    candidates.append(Path.home() / "AppData" / "Local" / Config.APP_DIR_NAME)
    candidates.append(get_base_path() / "data")

    for path in candidates:
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except OSError:
            continue

    fallback = Path.cwd() / "data"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def get_high_score_path() -> Path:
    return get_data_path() / Config.HIGH_SCORE_FILE


def get_settings_path() -> Path:
    return get_data_path() / Config.SETTINGS_FILE


def get_save_path() -> Path:
    return get_data_path() / Config.SAVE_FILE
