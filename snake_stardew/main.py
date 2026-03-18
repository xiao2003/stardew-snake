from __future__ import annotations

import pygame

from config import Config, get_base_path
from game import SnakeGame


def main() -> None:
    pygame.init()
    pygame.display.set_caption(Config.WINDOW_TITLE)

    width = Config.GRID_WIDTH * Config.TILE_SIZE
    height = Config.GRID_HEIGHT * Config.TILE_SIZE + Config.HUD_HEIGHT
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)

    icon_path = get_base_path() / "assets" / "stardew_style_icon.png"
    if icon_path.exists():
        try:
            icon_surface = pygame.image.load(str(icon_path)).convert_alpha()
            pygame.display.set_icon(icon_surface)
        except pygame.error:
            pass

    game = SnakeGame(screen)
    game.run()

    pygame.quit()


if __name__ == "__main__":
    main()
