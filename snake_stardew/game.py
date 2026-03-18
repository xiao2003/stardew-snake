from __future__ import annotations

import json
from pathlib import Path
import pygame

from config import Config, get_high_score_path, get_save_path, get_settings_path
from food import Food
from input_handler import InputFrame, InputHandler
from renderer import RenderSnapshot, Renderer
from snake import Snake
from state import BoundaryMode, GameState


Coord = tuple[int, int]


class SnakeGame:
    SPEED_CHOICES = [0.8, 1.0, 1.2, 1.4, 1.6]
    FRUIT_DELAY_CHOICES = [0, 1, 2, 3, 4]

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(screen)
        self.input_handler = InputHandler()

        self.is_fullscreen = False
        self.windowed_size = screen.get_size()

        self.state = GameState.MENU
        self.running = True

        self.score = 0
        self.high_score = self._load_high_score()

        self.boundary_mode = BoundaryMode.SOLID
        self.speed_index = 1
        self.fruit_delay_index = 0
        self._load_settings()

        self.menu_items = ["新游戏", "继续游戏", "设置", "退出"]
        self.menu_index = 0

        self.settings_items = ["边界模式", "蛇速度", "果子生成速度", "返回"]
        self.settings_index = 0

        self.pause_items = ["继续游戏", "回到欢迎界面"]
        self.pause_index = 0

        self.save_confirm_items = ["保存并返回", "不保存返回", "取消"]
        self.save_confirm_index = 0

        self.game_over_items = ["重新开始", "返回主菜单"]
        self.game_over_index = 0

        self.walkable_cells: set[Coord] = {
            (x, y)
            for y in range(1, Config.GRID_HEIGHT - 1)
            for x in range(1, Config.GRID_WIDTH - 1)
        }

        self.snake = self._create_snake()
        self.food = Food()
        self.step_accumulator = 0.0
        self.last_step_interval = 1.0 / Config.BASE_STEPS_PER_SECOND
        self.food_spawn_countdown_steps = 0
        self.wrap_transition = False
        self._spawn_food_now()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(Config.TARGET_FPS) / 1000.0
            inputs = self.input_handler.poll()

            if inputs.quit_requested:
                self.running = False
                continue

            self._handle_window_controls(inputs)

            if inputs.key == pygame.K_ESCAPE and self.state == GameState.MENU:
                self.running = False
                continue

            self._handle_state_input(inputs)

            if self.state == GameState.RUNNING:
                self._update_simulation(dt)

            progress = self._compute_progress()
            self._render(progress)
            pygame.display.flip()
            self.wrap_transition = False

        self._save_high_score_if_needed()
        self._save_settings()

    def _handle_window_controls(self, inputs: InputFrame) -> None:
        if inputs.resize_size is not None and not self.is_fullscreen:
            self._set_windowed(inputs.resize_size)

        if inputs.toggle_fullscreen:
            self._toggle_fullscreen()
            return

        if inputs.mouse_left_clicked and inputs.mouse_pos is not None:
            if self.renderer.is_toggle_button_hit(inputs.mouse_pos):
                self._toggle_fullscreen()

    def _set_windowed(self, size: tuple[int, int]) -> None:
        self.windowed_size = (max(640, size[0]), max(480, size[1]))
        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self.renderer.set_screen(self.screen)
        self.is_fullscreen = False

    def _set_fullscreen(self) -> None:
        self.windowed_size = self.screen.get_size()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.renderer.set_screen(self.screen)
        self.is_fullscreen = True

    def _toggle_fullscreen(self) -> None:
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
            self.renderer.set_screen(self.screen)
            self.is_fullscreen = False
        else:
            self._set_fullscreen()

    def _handle_state_input(self, inputs: InputFrame) -> None:
        if self.state == GameState.MENU:
            self._handle_menu_input(inputs)
        elif self.state == GameState.SETTINGS:
            self._handle_settings_input(inputs)
        elif self.state == GameState.PAUSED:
            self._handle_pause_input(inputs)
        elif self.state == GameState.SAVE_CONFIRM:
            self._handle_save_confirm_input(inputs)
        elif self.state == GameState.GAME_OVER:
            self._handle_game_over_input(inputs)
        elif self.state == GameState.RUNNING:
            self._handle_running_shortcuts(inputs)

    def _handle_running_shortcuts(self, inputs: InputFrame) -> None:
        if inputs.direction is not None:
            self.snake.set_direction(inputs.direction)

        if inputs.key in (pygame.K_p, pygame.K_SPACE, pygame.K_ESCAPE):
            self.state = GameState.PAUSED
            self.pause_index = 0

    def _handle_menu_input(self, inputs: InputFrame) -> None:
        if inputs.key in (pygame.K_UP, pygame.K_w):
            self.menu_index = (self.menu_index - 1) % len(self.menu_items)
            return
        if inputs.key in (pygame.K_DOWN, pygame.K_s):
            self.menu_index = (self.menu_index + 1) % len(self.menu_items)
            return

        if inputs.key not in (pygame.K_RETURN, pygame.K_SPACE):
            return

        selected = self.menu_items[self.menu_index]
        if selected == "新游戏":
            self._restart()
            self._clear_saved_session()
            self.state = GameState.RUNNING
        elif selected == "继续游戏":
            if self._load_saved_session():
                self.state = GameState.RUNNING
            else:
                self._restart()
                self.state = GameState.RUNNING
        elif selected == "设置":
            self.state = GameState.SETTINGS
            self.settings_index = 0
        else:
            self.running = False

    def _handle_settings_input(self, inputs: InputFrame) -> None:
        if inputs.key in (pygame.K_UP, pygame.K_w):
            self.settings_index = (self.settings_index - 1) % len(self.settings_items)
            return
        if inputs.key in (pygame.K_DOWN, pygame.K_s):
            self.settings_index = (self.settings_index + 1) % len(self.settings_items)
            return

        if inputs.key == pygame.K_ESCAPE:
            self._save_settings()
            self.state = GameState.MENU
            return

        if inputs.key in (pygame.K_LEFT, pygame.K_a):
            self._adjust_setting(-1)
            return
        if inputs.key in (pygame.K_RIGHT, pygame.K_d):
            self._adjust_setting(1)
            return

        if inputs.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.settings_index == 3:
                self._save_settings()
                self.state = GameState.MENU
            else:
                self._adjust_setting(1)

    def _adjust_setting(self, delta: int) -> None:
        if self.settings_index == 0:
            self.boundary_mode = BoundaryMode.WRAP if self.boundary_mode == BoundaryMode.SOLID else BoundaryMode.SOLID
        elif self.settings_index == 1:
            n = len(self.SPEED_CHOICES)
            self.speed_index = (self.speed_index + delta) % n
        elif self.settings_index == 2:
            n = len(self.FRUIT_DELAY_CHOICES)
            self.fruit_delay_index = (self.fruit_delay_index + delta) % n
        self._save_settings()

    def _handle_pause_input(self, inputs: InputFrame) -> None:
        if inputs.key in (pygame.K_UP, pygame.K_w):
            self.pause_index = (self.pause_index - 1) % len(self.pause_items)
            return
        if inputs.key in (pygame.K_DOWN, pygame.K_s):
            self.pause_index = (self.pause_index + 1) % len(self.pause_items)
            return

        if inputs.key in (pygame.K_p, pygame.K_SPACE):
            self.state = GameState.RUNNING
            return

        if inputs.key == pygame.K_ESCAPE:
            self.state = GameState.SAVE_CONFIRM
            self.save_confirm_index = 0
            return

        if inputs.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.pause_index == 0:
                self.state = GameState.RUNNING
            else:
                self.state = GameState.SAVE_CONFIRM
                self.save_confirm_index = 0

    def _handle_save_confirm_input(self, inputs: InputFrame) -> None:
        if inputs.key in (pygame.K_UP, pygame.K_w):
            self.save_confirm_index = (self.save_confirm_index - 1) % len(self.save_confirm_items)
            return
        if inputs.key in (pygame.K_DOWN, pygame.K_s):
            self.save_confirm_index = (self.save_confirm_index + 1) % len(self.save_confirm_items)
            return

        if inputs.key == pygame.K_ESCAPE:
            self.state = GameState.PAUSED
            return

        if inputs.key not in (pygame.K_RETURN, pygame.K_SPACE):
            return

        if self.save_confirm_index == 0:
            self._save_session()
            self.state = GameState.MENU
        elif self.save_confirm_index == 1:
            self._clear_saved_session()
            self.state = GameState.MENU
        else:
            self.state = GameState.PAUSED

    def _handle_game_over_input(self, inputs: InputFrame) -> None:
        if inputs.key in (pygame.K_UP, pygame.K_w):
            self.game_over_index = (self.game_over_index - 1) % len(self.game_over_items)
            return
        if inputs.key in (pygame.K_DOWN, pygame.K_s):
            self.game_over_index = (self.game_over_index + 1) % len(self.game_over_items)
            return

        if inputs.key == pygame.K_ESCAPE:
            self.state = GameState.MENU
            return

        if inputs.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.game_over_index == 0:
                self._restart()
                self.state = GameState.RUNNING
            else:
                self.state = GameState.MENU

    def _update_simulation(self, dt: float) -> None:
        speed_scale = self.SPEED_CHOICES[self.speed_index]
        speed = min(
            Config.MAX_STEPS_PER_SECOND,
            (Config.BASE_STEPS_PER_SECOND + self.score * Config.SPEED_PER_FOOD) * speed_scale,
        )

        self.last_step_interval = 1.0 / speed
        self.step_accumulator += dt

        wrapped_any = False
        while self.step_accumulator >= self.last_step_interval and self.state == GameState.RUNNING:
            self.step_accumulator -= self.last_step_interval
            wrapped_any = self._step_logic() or wrapped_any
        self.wrap_transition = wrapped_any

    def _step_logic(self) -> bool:
        raw_next = self.snake.next_head()

        if self.boundary_mode == BoundaryMode.SOLID and raw_next not in self.walkable_cells:
            self.state = GameState.GAME_OVER
            self.game_over_index = 0
            return False

        next_head = self._normalize_cell(raw_next)
        wrapped = self.boundary_mode == BoundaryMode.WRAP and next_head != raw_next
        eating = self.food.position is not None and next_head == self.food.position

        if self._is_body_collision(next_head, eating):
            self.state = GameState.GAME_OVER
            self.game_over_index = 0
            return False

        if eating:
            self.snake.grow(1)

        self.snake.step(forced_head=next_head)
        if wrapped:
            # Avoid long interpolation across map when wrapping.
            self.snake.prev_head = self.snake.head

        if eating:
            self.score += 1
            if self.score > self.high_score:
                self.high_score = self.score

            self.food.position = None
            self.food_spawn_countdown_steps = self.FRUIT_DELAY_CHOICES[self.fruit_delay_index]

        if self.food.position is None:
            if self.food_spawn_countdown_steps > 0:
                self.food_spawn_countdown_steps -= 1
            if self.food_spawn_countdown_steps == 0:
                if self._spawn_food_now() is None:
                    self.state = GameState.GAME_OVER
                    self.game_over_index = 0
                    return wrapped
        return wrapped

    def _spawn_food_now(self) -> Coord | None:
        return self.food.spawn_in_walkable(self.walkable_cells, self.snake.body_set)

    def _normalize_cell(self, cell: Coord) -> Coord:
        if self.boundary_mode == BoundaryMode.SOLID:
            return cell

        min_x, max_x = 1, Config.GRID_WIDTH - 2
        min_y, max_y = 1, Config.GRID_HEIGHT - 2

        x, y = cell
        if x < min_x:
            x = max_x
        elif x > max_x:
            x = min_x

        if y < min_y:
            y = max_y
        elif y > max_y:
            y = min_y

        return (x, y)

    def _is_body_collision(self, next_head: Coord, eating: bool) -> bool:
        if next_head not in self.snake.body_set:
            return False

        if next_head == self.snake.tail and self.snake.grow_pending == 0 and not eating:
            return False

        return True

    def _compute_progress(self) -> float:
        if self.state != GameState.RUNNING:
            return 1.0
        if self.last_step_interval <= 0:
            return 1.0
        return min(1.0, self.step_accumulator / self.last_step_interval)

    def _render(self, progress: float) -> None:
        snapshot = RenderSnapshot(
            state=self.state,
            score=self.score,
            high_score=self.high_score,
            progress=progress,
            snake_cells=list(self.snake.body),
            snake_prev_head=self.snake.prev_head,
            snake_prev_tail=self.snake.prev_tail,
            snake_growing=self.snake.grow_pending > 0,
            food=self.food.position,
            boundary_mode=self.boundary_mode,
            menu_items=self.menu_items,
            menu_index=self.menu_index,
            settings_items=self.settings_items,
            settings_index=self.settings_index,
            game_over_items=self.game_over_items,
            game_over_index=self.game_over_index,
            can_continue=self._has_saved_session(),
            pause_items=self.pause_items,
            pause_index=self.pause_index,
            save_confirm_items=self.save_confirm_items,
            save_confirm_index=self.save_confirm_index,
            speed_label=self._speed_label(),
            fruit_speed_label=self._fruit_speed_label(),
            is_fullscreen=self.is_fullscreen,
            wrap_transition=self.wrap_transition,
        )
        self.renderer.draw(snapshot)

    def _restart(self) -> None:
        self.snake = self._create_snake()
        self.food = Food()
        self.score = 0
        self.step_accumulator = 0.0
        self.last_step_interval = 1.0 / Config.BASE_STEPS_PER_SECOND
        self.food_spawn_countdown_steps = 0
        self._spawn_food_now()

    def _create_snake(self) -> Snake:
        start = (Config.GRID_WIDTH // 2, Config.GRID_HEIGHT // 2)
        return Snake(start=start, initial_length=4, direction=(1, 0))

    def _load_high_score(self) -> int:
        path = get_high_score_path()
        if not path.exists():
            return 0

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            value = int(raw.get("high_score", 0))
            return max(0, value)
        except (json.JSONDecodeError, OSError, ValueError, TypeError):
            return 0

    def _save_high_score_if_needed(self) -> None:
        path: Path = get_high_score_path()
        current = self._load_high_score()
        if self.high_score <= current:
            return

        payload = {"high_score": self.high_score}
        try:
            path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _load_settings(self) -> None:
        path = get_settings_path()
        if not path.exists():
            return

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.boundary_mode = BoundaryMode(str(raw.get("boundary_mode", BoundaryMode.SOLID.value)))
            self.speed_index = int(raw.get("speed_index", self.speed_index))
            self.fruit_delay_index = int(raw.get("fruit_delay_index", self.fruit_delay_index))
            self.speed_index = max(0, min(self.speed_index, len(self.SPEED_CHOICES) - 1))
            self.fruit_delay_index = max(0, min(self.fruit_delay_index, len(self.FRUIT_DELAY_CHOICES) - 1))
        except (json.JSONDecodeError, OSError, ValueError, TypeError):
            self.boundary_mode = BoundaryMode.SOLID
            self.speed_index = 1
            self.fruit_delay_index = 0

    def _save_settings(self) -> None:
        path = get_settings_path()
        payload = {
            "boundary_mode": self.boundary_mode.value,
            "speed_index": self.speed_index,
            "fruit_delay_index": self.fruit_delay_index,
        }
        try:
            path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _save_session(self) -> None:
        path = get_save_path()
        payload = {
            "snake": list(self.snake.body),
            "direction": list(self.snake.direction),
            "next_direction": list(self.snake.next_direction),
            "score": self.score,
            "food": list(self.food.position) if self.food.position is not None else None,
            "food_delay": self.food_spawn_countdown_steps,
        }
        try:
            path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _load_saved_session(self) -> bool:
        path = get_save_path()
        if not path.exists():
            return False

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            body_raw = raw.get("snake")
            if not isinstance(body_raw, list) or len(body_raw) < 2:
                return False

            body: list[Coord] = []
            for cell in body_raw:
                if not isinstance(cell, list) or len(cell) != 2:
                    return False
                point = (int(cell[0]), int(cell[1]))
                if point not in self.walkable_cells:
                    return False
                body.append(point)

            self.snake = Snake(start=body[0], initial_length=2, direction=(1, 0))
            from collections import deque
            self.snake.body = deque(body)
            self.snake.body_set = set(body)
            self.snake.direction = tuple(raw.get("direction", [1, 0]))  # type: ignore[assignment]
            self.snake.next_direction = tuple(raw.get("next_direction", [1, 0]))  # type: ignore[assignment]
            self.snake.prev_head = self.snake.head
            self.snake.prev_tail = self.snake.tail
            self.snake.grow_pending = 0

            self.score = int(raw.get("score", 0))
            self.food = Food()
            food_raw = raw.get("food")
            if isinstance(food_raw, list) and len(food_raw) == 2:
                food_point = (int(food_raw[0]), int(food_raw[1]))
                self.food.position = food_point if food_point in self.walkable_cells else None
            else:
                self.food.position = None

            self.food_spawn_countdown_steps = max(0, int(raw.get("food_delay", 0)))

            self.step_accumulator = 0.0
            self.last_step_interval = 1.0 / Config.BASE_STEPS_PER_SECOND
            self.wrap_transition = False
            return True
        except (json.JSONDecodeError, OSError, ValueError, TypeError):
            return False

    def _has_saved_session(self) -> bool:
        return get_save_path().exists()

    def _clear_saved_session(self) -> None:
        path = get_save_path()
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass

    def _speed_label(self) -> str:
        return f"{int(self.SPEED_CHOICES[self.speed_index] * 100)}%"

    def _fruit_speed_label(self) -> str:
        delay = self.FRUIT_DELAY_CHOICES[self.fruit_delay_index]
        if delay == 0:
            return "快"
        if delay <= 2:
            return "中"
        return "慢"
