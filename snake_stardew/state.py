from __future__ import annotations

from enum import Enum


class GameState(Enum):
    MENU = "menu"
    RUNNING = "running"
    PAUSED = "paused"
    SETTINGS = "settings"
    GAME_OVER = "game_over"
    SAVE_CONFIRM = "save_confirm"


class BoundaryMode(Enum):
    SOLID = "solid"
    WRAP = "wrap"
