from __future__ import annotations

from collections import deque


Coord = tuple[int, int]
Direction = tuple[int, int]


class Snake:
    def __init__(self, start: Coord, initial_length: int = 4, direction: Direction = (1, 0)) -> None:
        self.direction: Direction = direction
        self.next_direction: Direction = direction

        body = [start]
        for i in range(1, initial_length):
            body.append((start[0] - i, start[1]))

        self.body: deque[Coord] = deque(body)
        self.body_set: set[Coord] = set(body)

        self.grow_pending = 0

        self.prev_head: Coord = self.head
        self.prev_tail: Coord = self.tail
        self.last_removed_tail: Coord | None = None

    @property
    def head(self) -> Coord:
        return self.body[0]

    @property
    def tail(self) -> Coord:
        return self.body[-1]

    @staticmethod
    def is_opposite(a: Direction, b: Direction) -> bool:
        return a[0] == -b[0] and a[1] == -b[1]

    def set_direction(self, new_direction: Direction) -> None:
        if new_direction == self.next_direction:
            return
        if self.is_opposite(new_direction, self.direction):
            return
        self.next_direction = new_direction

    def next_head(self) -> Coord:
        return (self.head[0] + self.next_direction[0], self.head[1] + self.next_direction[1])

    def step(self, forced_head: Coord | None = None) -> Coord:
        self.prev_head = self.head
        self.prev_tail = self.tail

        self.direction = self.next_direction
        new_head = forced_head if forced_head is not None else (self.head[0] + self.direction[0], self.head[1] + self.direction[1])

        self.body.appendleft(new_head)
        self.body_set.add(new_head)

        self.last_removed_tail = None
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            removed = self.body.pop()
            self.body_set.remove(removed)
            self.last_removed_tail = removed

        return new_head

    def grow(self, amount: int = 1) -> None:
        self.grow_pending += amount

    def occupies(self, cell: Coord) -> bool:
        return cell in self.body_set
