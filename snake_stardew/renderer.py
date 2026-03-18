from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pygame

from config import Config, get_base_path
from state import BoundaryMode, GameState


Coord = tuple[int, int]


@dataclass
class RenderSnapshot:
    state: GameState
    score: int
    high_score: int
    progress: float
    snake_cells: list[Coord]
    snake_prev_head: Coord
    snake_prev_tail: Coord
    snake_growing: bool
    food: Coord | None
    boundary_mode: BoundaryMode
    menu_items: list[str]
    menu_index: int
    settings_items: list[str]
    settings_index: int
    game_over_items: list[str]
    game_over_index: int
    can_continue: bool
    pause_items: list[str]
    pause_index: int
    save_confirm_items: list[str]
    save_confirm_index: int
    speed_label: str
    fruit_speed_label: str
    is_fullscreen: bool
    wrap_transition: bool


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.tile = Config.TILE_SIZE
        self.hud_h = Config.HUD_HEIGHT

        self.logical_w = Config.GRID_WIDTH * self.tile
        self.logical_h = Config.GRID_HEIGHT * self.tile + self.hud_h
        self.canvas = pygame.Surface((self.logical_w, self.logical_h), pygame.SRCALPHA)

        self.viewport_rect = pygame.Rect(0, 0, self.logical_w, self.logical_h)
        self.window_toggle_rect = pygame.Rect(0, 0, 0, 0)

        self.font_title = pygame.font.SysFont(Config.FONT_NAME, 40, bold=True)
        self.font_main = pygame.font.SysFont(Config.FONT_NAME, 24, bold=True)
        self.font_small = pygame.font.SysFont(Config.FONT_NAME, 18)

        self.ground_tiles = self._build_ground_tiles(self.tile)
        self.border_tile = self._build_border_tile(self.tile)
        self.snake_head_sprite = self._build_snake_head_sprite(self.tile)
        self.snake_body_sprite = self._build_snake_body_sprite(self.tile)
        self.food_sprite = self._build_food_sprite(self.tile)
        self.hud_icon = self._load_hud_icon()

    def set_screen(self, screen: pygame.Surface) -> None:
        self.screen = screen

    def is_toggle_button_hit(self, pos: tuple[int, int]) -> bool:
        return self.window_toggle_rect.collidepoint(pos)

    def draw(self, snapshot: RenderSnapshot) -> None:
        if snapshot.state in (GameState.MENU, GameState.SETTINGS):
            self._draw_app_shell(snapshot)
        else:
            self._draw_background()
            self._draw_grid()
            self._draw_food(snapshot.food)
            self._draw_snake(snapshot)
            self._draw_hud(snapshot)
            self._draw_overlay(snapshot)

        self._present_canvas()
        self._draw_window_button(snapshot.is_fullscreen)

    def _draw_background(self) -> None:
        top = pygame.Color(190, 224, 170)
        bottom = pygame.Color(121, 166, 104)
        for y in range(self.logical_h):
            t = y / max(1, self.logical_h - 1)
            r = int(top.r + (bottom.r - top.r) * t)
            g = int(top.g + (bottom.g - top.g) * t)
            b = int(top.b + (bottom.b - top.b) * t)
            pygame.draw.line(self.canvas, (r, g, b), (0, y), (self.logical_w, y))

        # Distant rolling hills for a stronger farm atmosphere.
        pygame.draw.ellipse(
            self.canvas,
            (124, 170, 99),
            pygame.Rect(-120, self.hud_h + 35, self.logical_w // 2 + 220, 120),
        )
        pygame.draw.ellipse(
            self.canvas,
            (112, 156, 90),
            pygame.Rect(self.logical_w // 3, self.hud_h + 22, self.logical_w // 2 + 260, 150),
        )

    def _draw_grid(self) -> None:
        for y in range(Config.GRID_HEIGHT):
            for x in range(Config.GRID_WIDTH):
                tile = self.ground_tiles[(x + y) % len(self.ground_tiles)]
                self.canvas.blit(tile, (x * self.tile, self.hud_h + y * self.tile))

        for x in range(Config.GRID_WIDTH):
            self.canvas.blit(self.border_tile, (x * self.tile, self.hud_h))
            self.canvas.blit(self.border_tile, (x * self.tile, self.hud_h + (Config.GRID_HEIGHT - 1) * self.tile))

        for y in range(Config.GRID_HEIGHT):
            self.canvas.blit(self.border_tile, (0, self.hud_h + y * self.tile))
            self.canvas.blit(self.border_tile, ((Config.GRID_WIDTH - 1) * self.tile, self.hud_h + y * self.tile))

    def _grid_to_px(self, cell: Coord) -> tuple[float, float]:
        return (cell[0] * self.tile, self.hud_h + cell[1] * self.tile)

    def _draw_food(self, food: Coord | None) -> None:
        if food is None:
            return
        px, py = self._grid_to_px(food)
        self.canvas.blit(self.food_sprite, (px, py))

    def _draw_snake(self, snapshot: RenderSnapshot) -> None:
        if not snapshot.snake_cells:
            return

        if snapshot.wrap_transition:
            for i, cell in enumerate(snapshot.snake_cells):
                cx, cy = self._grid_to_px(cell)
                if i == 0:
                    self.canvas.blit(self.snake_head_sprite, (cx, cy))
                else:
                    self.canvas.blit(self.snake_body_sprite, (cx, cy))
            return

        interp = max(0.0, min(1.0, snapshot.progress))
        for i, cell in enumerate(snapshot.snake_cells):
            cx, cy = self._grid_to_px(cell)

            if i == 0:
                prev_x, prev_y = self._grid_to_px(snapshot.snake_prev_head)
                draw_x = prev_x + (cx - prev_x) * interp
                draw_y = prev_y + (cy - prev_y) * interp
                self.canvas.blit(self.snake_head_sprite, (draw_x, draw_y))
                continue

            if i == len(snapshot.snake_cells) - 1 and not snapshot.snake_growing:
                prev_tail_x, prev_tail_y = self._grid_to_px(snapshot.snake_prev_tail)
                draw_x = cx + (prev_tail_x - cx) * (1.0 - interp)
                draw_y = cy + (prev_tail_y - cy) * (1.0 - interp)
                self.canvas.blit(self.snake_body_sprite, (draw_x, draw_y))
                continue

            self.canvas.blit(self.snake_body_sprite, (cx, cy))

    def _draw_hud(self, snapshot: RenderSnapshot) -> None:
        hud_rect = pygame.Rect(0, 0, self.logical_w, self.hud_h)
        pygame.draw.rect(self.canvas, (118, 84, 59), hud_rect)
        pygame.draw.rect(self.canvas, (151, 113, 81), pygame.Rect(0, 0, self.logical_w, 8))
        pygame.draw.rect(self.canvas, (92, 66, 46), pygame.Rect(0, self.hud_h - 8, self.logical_w, 8))

        boundary_text = "撞墙死亡" if snapshot.boundary_mode == BoundaryMode.SOLID else "穿墙模式"
        title = self.font_main.render("星露谷风贪吃蛇", True, Config.COLOR_ACCENT)
        score_text = self.font_small.render(f"分数: {snapshot.score}", True, (242, 233, 205))
        high_text = self.font_small.render(f"最高分: {snapshot.high_score}", True, (242, 233, 205))
        state_text = self.font_small.render(f"状态: {self._state_text(snapshot.state)}", True, (242, 233, 205))
        mode_text = self.font_small.render(f"边界: {boundary_text}", True, (242, 233, 205))

        self.canvas.blit(title, (64, 8))
        self.canvas.blit(score_text, (16, 40))
        self.canvas.blit(high_text, (130, 40))
        self.canvas.blit(state_text, (270, 40))
        self.canvas.blit(mode_text, (430, 40))
        if self.hud_icon is not None:
            self.canvas.blit(self.hud_icon, (16, 8))

    def _draw_overlay(self, snapshot: RenderSnapshot) -> None:
        if snapshot.state == GameState.RUNNING:
            return

        overlay = pygame.Surface((self.logical_w, self.logical_h - self.hud_h), pygame.SRCALPHA)
        overlay.fill((20, 20, 18, 150))
        self.canvas.blit(overlay, (0, self.hud_h))

        if snapshot.state == GameState.PAUSED:
            self._draw_pause_menu(snapshot)
        elif snapshot.state == GameState.SAVE_CONFIRM:
            self._draw_save_confirm(snapshot)
        elif snapshot.state == GameState.GAME_OVER:
            self._draw_game_over(snapshot)

    def _draw_app_shell(self, snapshot: RenderSnapshot) -> None:
        self.canvas.fill((158, 202, 132))

        for y in range(0, self.logical_h, 18):
            pygame.draw.line(self.canvas, (146, 188, 120), (0, y), (self.logical_w, y), 1)

        # Soft clouds.
        pygame.draw.ellipse(self.canvas, (234, 243, 220), pygame.Rect(70, 28, 120, 36))
        pygame.draw.ellipse(self.canvas, (234, 243, 220), pygame.Rect(130, 24, 90, 32))
        pygame.draw.ellipse(self.canvas, (234, 243, 220), pygame.Rect(470, 34, 130, 38))
        pygame.draw.ellipse(self.canvas, (234, 243, 220), pygame.Rect(545, 30, 95, 34))

        card_shadow = pygame.Rect(self.logical_w // 2 - 258, self.hud_h + 52, 516, self.logical_h - self.hud_h - 104)
        pygame.draw.rect(self.canvas, (68, 49, 37), card_shadow, border_radius=18)
        panel = card_shadow.inflate(-10, -10)
        pygame.draw.rect(self.canvas, (114, 82, 58), panel, border_radius=16)
        inner = panel.inflate(-14, -14)
        pygame.draw.rect(self.canvas, (142, 104, 74), inner, border_radius=12)

        # Top ribbon.
        ribbon = pygame.Rect(inner.x + 20, inner.y + 14, inner.width - 40, 28)
        pygame.draw.rect(self.canvas, (178, 141, 98), ribbon, border_radius=10)
        pygame.draw.rect(self.canvas, (96, 70, 49), ribbon, 2, border_radius=10)

        if self.hud_icon is not None:
            icon = pygame.transform.scale(self.hud_icon, (72, 72))
            self.canvas.blit(icon, (panel.x + 24, panel.y + 18))

        title = self.font_title.render("星露谷风贪吃蛇", True, (255, 243, 192))
        self.canvas.blit(title, (panel.x + 118, panel.y + 28))

        if snapshot.state == GameState.MENU:
            hint = self.font_small.render("上下选择，回车确认", True, (238, 224, 185))
            self.canvas.blit(hint, (panel.x + 160, panel.y + 86))
            self._draw_app_menu_items(snapshot, inner)
        else:
            hint = self.font_small.render("左右或回车切换，ESC 返回", True, (238, 224, 185))
            self.canvas.blit(hint, (panel.x + 140, panel.y + 86))
            self._draw_app_settings_items(snapshot, inner)

    def _draw_app_menu_items(self, snapshot: RenderSnapshot, inner: pygame.Rect) -> None:
        start_y = inner.y + 130
        for i, item in enumerate(snapshot.menu_items):
            is_sel = i == snapshot.menu_index
            disabled = item == "继续游戏" and not snapshot.can_continue
            color = (245, 234, 196)
            if disabled:
                color = (168, 161, 145)
            if is_sel and not disabled:
                color = (255, 247, 166)

            text = self.font_main.render(("> " if is_sel else "  ") + item, True, color)
            x = inner.x + (inner.width - text.get_width()) // 2
            y = start_y + i * 46
            self.canvas.blit(text, (x, y))

    def _draw_app_settings_items(self, snapshot: RenderSnapshot, inner: pygame.Rect) -> None:
        boundary_value = "撞墙死亡" if snapshot.boundary_mode == BoundaryMode.SOLID else "穿墙模式"
        rows = [
            f"边界模式: {boundary_value}",
            f"蛇速度: {snapshot.speed_label}",
            f"果子生成速度: {snapshot.fruit_speed_label}",
            "返回主菜单",
        ]

        start_y = inner.y + 130
        for i, row in enumerate(rows):
            is_sel = i == snapshot.settings_index
            color = (255, 247, 166) if is_sel else (245, 234, 196)
            text = self.font_main.render(("> " if is_sel else "  ") + row, True, color)
            x = inner.x + (inner.width - text.get_width()) // 2
            y = start_y + i * 44
            self.canvas.blit(text, (x, y))

    def _draw_pause_menu(self, snapshot: RenderSnapshot) -> None:
        self._draw_center_title("已暂停", -120)
        self._draw_center_hint("空格/P 继续；ESC 进入返回确认", -80)
        self._draw_center_options(snapshot.pause_items, snapshot.pause_index, -20)

    def _draw_save_confirm(self, snapshot: RenderSnapshot) -> None:
        self._draw_center_title("返回欢迎界面", -120)
        self._draw_center_hint("是否保存当前进度？", -80)
        self._draw_center_options(snapshot.save_confirm_items, snapshot.save_confirm_index, -20)

    def _draw_game_over(self, snapshot: RenderSnapshot) -> None:
        self._draw_center_title("游戏结束", -120)
        self._draw_center_hint("上下选择，回车确认", -80)
        self._draw_center_options(snapshot.game_over_items, snapshot.game_over_index, -20)

    def _draw_center_options(self, items: list[str], selected: int, offset_y: int) -> None:
        start_y = self.hud_h + (self.logical_h - self.hud_h) // 2 + offset_y
        for i, item in enumerate(items):
            is_sel = i == selected
            color = (255, 247, 166) if is_sel else (245, 234, 196)
            text = self.font_main.render(("> " if is_sel else "  ") + item, True, color)
            x = (self.logical_w - text.get_width()) // 2
            y = start_y + i * 44
            self.canvas.blit(text, (x, y))

    def _draw_center_title(self, text: str, offset_y: int) -> None:
        surf = self.font_title.render(text, True, (255, 245, 201))
        x = (self.logical_w - surf.get_width()) // 2
        y = self.hud_h + (self.logical_h - self.hud_h) // 2 + offset_y
        self.canvas.blit(surf, (x, y))

    def _draw_center_hint(self, text: str, offset_y: int) -> None:
        surf = self.font_small.render(text, True, (241, 230, 187))
        x = (self.logical_w - surf.get_width()) // 2
        y = self.hud_h + (self.logical_h - self.hud_h) // 2 + offset_y
        self.canvas.blit(surf, (x, y))

    def _present_canvas(self) -> None:
        self.screen.fill((34, 30, 28))
        sw, sh = self.screen.get_size()
        scale = min(sw / self.logical_w, sh / self.logical_h)
        scale = max(scale, 0.1)

        target_w = int(self.logical_w * scale)
        target_h = int(self.logical_h * scale)
        x = (sw - target_w) // 2
        y = (sh - target_h) // 2

        self.viewport_rect = pygame.Rect(x, y, target_w, target_h)

        scaled = pygame.transform.smoothscale(self.canvas, (target_w, target_h))
        self.screen.blit(scaled, (x, y))

    def _draw_window_button(self, is_fullscreen: bool) -> None:
        text = "窗口" if is_fullscreen else "全屏"
        font = self.font_small
        label = font.render(text, True, (245, 238, 216))

        padding_x = 12
        padding_y = 6
        w = label.get_width() + padding_x * 2
        h = label.get_height() + padding_y * 2

        margin = 14
        rect = pygame.Rect(
            self.screen.get_width() - w - margin,
            margin,
            w,
            h,
        )
        self.window_toggle_rect = rect

        pygame.draw.rect(self.screen, (92, 68, 50), rect, border_radius=8)
        pygame.draw.rect(self.screen, (157, 123, 92), rect, 2, border_radius=8)
        self.screen.blit(label, (rect.x + padding_x, rect.y + padding_y))

    def _build_ground_tiles(self, size: int) -> list[pygame.Surface]:
        tiles: list[pygame.Surface] = []
        colors = [(142, 188, 120), (136, 182, 115), (148, 194, 124)]
        for base in colors:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            surf.fill(base)
            pygame.draw.rect(surf, (122, 168, 103), pygame.Rect(0, 0, size, size), 1)
            pygame.draw.rect(surf, (113, 159, 94), pygame.Rect(size // 5, size // 4, 2, 2))
            pygame.draw.rect(surf, (113, 159, 94), pygame.Rect(size // 2, size // 2, 2, 2))
            pygame.draw.rect(surf, (113, 159, 94), pygame.Rect(size - 7, size // 3, 2, 2))
            tiles.append(surf)
        return tiles

    def _build_border_tile(self, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((107, 74, 52))
        pygame.draw.rect(surf, (90, 62, 43), pygame.Rect(0, 0, size, size), 2)
        pygame.draw.rect(surf, (130, 95, 65), pygame.Rect(4, 4, size - 8, size - 8), 1)
        return surf

    def _build_snake_head_sprite(self, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(surf, Config.COLOR_SNAKE_HEAD, pygame.Rect(2, 2, size - 4, size - 4), border_radius=5)
        pygame.draw.rect(surf, (58, 104, 58), pygame.Rect(3, 3, size - 6, size - 6), 2, border_radius=5)
        eye_w = max(2, size // 8)
        pygame.draw.rect(surf, (230, 240, 219), pygame.Rect(size // 4, size // 3, eye_w, eye_w))
        pygame.draw.rect(surf, (230, 240, 219), pygame.Rect(size // 2, size // 3, eye_w, eye_w))
        return surf

    def _build_snake_body_sprite(self, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(surf, Config.COLOR_SNAKE_BODY, pygame.Rect(3, 3, size - 6, size - 6), border_radius=6)
        pygame.draw.rect(surf, Config.COLOR_SNAKE_BELLY, pygame.Rect(6, size // 2, size - 12, max(3, size // 5)), border_radius=4)
        return surf

    def _build_food_sprite(self, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surf, Config.COLOR_FOOD_MAIN, (size // 2, size // 2 + 2), size // 3)
        pygame.draw.rect(surf, (190, 72, 60), pygame.Rect(size // 2 - 3, size // 2, 6, 6))
        pygame.draw.polygon(
            surf,
            Config.COLOR_FOOD_LEAF,
            [(size // 2, size // 2 - 10), (size // 2 + 10, size // 2 - 14), (size // 2 + 6, size // 2 - 4)],
        )
        return surf

    def _load_hud_icon(self) -> pygame.Surface | None:
        icon_path: Path = get_base_path() / "assets" / "stardew_style_icon.png"
        if not icon_path.exists():
            return None
        try:
            icon = pygame.image.load(str(icon_path)).convert_alpha()
            return pygame.transform.scale(icon, (44, 44))
        except pygame.error:
            return None

    @staticmethod
    def _state_text(state: GameState) -> str:
        if state == GameState.MENU:
            return "欢迎界面"
        if state == GameState.RUNNING:
            return "进行中"
        if state == GameState.PAUSED:
            return "已暂停"
        if state == GameState.SETTINGS:
            return "设置"
        if state == GameState.SAVE_CONFIRM:
            return "返回确认"
        return "已结束"
