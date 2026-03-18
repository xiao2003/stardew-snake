from __future__ import annotations

from dataclasses import dataclass
import pygame


Direction = tuple[int, int]
Size = tuple[int, int]


@dataclass
class InputFrame:
    direction: Direction | None = None
    key: int | None = None
    quit_requested: bool = False
    toggle_fullscreen: bool = False
    resize_size: Size | None = None
    mouse_left_clicked: bool = False
    mouse_pos: tuple[int, int] | None = None


class InputHandler:
    _DIR_KEYS: dict[int, Direction] = {
        pygame.K_UP: (0, -1),
        pygame.K_w: (0, -1),
        pygame.K_DOWN: (0, 1),
        pygame.K_s: (0, 1),
        pygame.K_LEFT: (-1, 0),
        pygame.K_a: (-1, 0),
        pygame.K_RIGHT: (1, 0),
        pygame.K_d: (1, 0),
    }

    def poll(self) -> InputFrame:
        result = InputFrame()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                result.quit_requested = True
                continue

            if event.type == pygame.VIDEORESIZE:
                result.resize_size = (max(640, int(event.w)), max(480, int(event.h)))
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                result.mouse_left_clicked = True
                result.mouse_pos = (int(event.pos[0]), int(event.pos[1]))
                continue

            if event.type != pygame.KEYDOWN:
                continue

            result.key = event.key
            if event.key in self._DIR_KEYS:
                result.direction = self._DIR_KEYS[event.key]
            if event.key == pygame.K_F11:
                result.toggle_fullscreen = True

        return result
