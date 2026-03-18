from __future__ import annotations

import random


Coord = tuple[int, int]


class Food:
    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.position: Coord | None = None

    def spawn_in_walkable(self, walkable: set[Coord], blocked: set[Coord]) -> Coord | None:
        free_cells = [cell for cell in walkable if cell not in blocked]
        if not free_cells:
            self.position = None
            return None

        self.position = self.rng.choice(free_cells)
        return self.position
