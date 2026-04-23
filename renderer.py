"""
renderer.py — Pygame rendering engine for the Hybrid Maze Game.

Layout:
  ┌──────────────────────────────────────────┐
  │  LEFT PANEL (controls)  │  MAZE VIEWPORT  │
  └──────────────────────────────────────────┘
"""

import pygame
from typing import List, Tuple, Optional
from maze import Maze
from game_state import GameState


# ── Palette ───────────────────────────────────────────────────────────
# ── Palette ───────────────────────────────────────────────────────────
C_BG          = (15,  17,  26)
C_WALL        = (32,  36,  52)
C_PATH        = (22,  25,  38)
C_PANEL       = (20,  24,  36)
C_PANEL_BORDER= (50,  60,  90)

C_PLAYER      = ( 80, 220, 150)   # soft emerald
C_ENEMY       = (240,  90, 110)   # soft coral
C_GOAL        = ( 80, 180, 240)   # sky blue
C_START       = (140, 120, 255)   # light violet

C_PLAYER_TRAIL= ( 80, 220, 150, 35)
C_ENEMY_TRAIL = (240,  90, 110, 35)
C_PATH_HIGHLIGHT=( 80, 180, 240, 80)

C_TEXT        = (220, 225, 245)
C_TEXT_DIM    = (130, 135, 160)
C_ACCENT      = ( 80, 180, 240)
C_WIN         = ( 80, 220, 150)
C_LOSE        = (240,  90, 110)

C_BTN         = (40,  46,  68)
C_BTN_HOVER   = (55,  62,  90)
C_BTN_ACTIVE  = ( 80, 180, 240)
C_BTN_TEXT    = (230, 235, 255)
C_BTN_BORDER  = (65,  75, 110)

PANEL_W       = 260
MIN_CELL_PX   = 12
MAX_CELL_PX   = 48
AGENT_RADIUS  = 0.38      # fraction of cell size


class Button:
    def __init__(self, rect: pygame.Rect, label: str, tag: str = ""):
        self.rect   = rect
        self.label  = label
        self.tag    = tag
        self.hovered= False
        self.active = False

    def draw(self, surf: pygame.Surface, font: pygame.font.Font):
        col = C_BTN_ACTIVE if self.active else (C_BTN_HOVER if self.hovered else C_BTN)
        # Main body
        pygame.draw.rect(surf, col, self.rect, border_radius=8)
        # Border
        b_col = C_ACCENT if (self.hovered or self.active) else C_BTN_BORDER
        pygame.draw.rect(surf, b_col, self.rect, 1, border_radius=8)
        # Shadow/Inner glow
        if self.hovered:
            s = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(s, (255, 255, 255, 15), s.get_rect(), border_radius=8)
            surf.blit(s, self.rect)
            
        txt = font.render(self.label, True, C_BTN_TEXT)
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def check_hover(self, pos: Tuple[int, int]):
        self.hovered = self.rect.collidepoint(pos)

    def clicked(self, pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


class Dropdown:
    def __init__(self, rect: pygame.Rect, options: List[str], selected: int = 0):
        self.rect     = rect
        self.options  = options
        self.selected = selected
        self.open     = False
        self.item_h   = rect.height

    def draw(self, surf: pygame.Surface, font: pygame.font.Font, mouse_pos):
        # Main box
        col = C_BTN_HOVER if self.rect.collidepoint(mouse_pos) else C_BTN
        pygame.draw.rect(surf, col, self.rect, border_radius=6)
        pygame.draw.rect(surf, C_BTN_BORDER, self.rect, 1, border_radius=6)
        label = font.render(self.options[self.selected], True, C_TEXT)
        surf.blit(label, label.get_rect(midleft=(self.rect.x + 10, self.rect.centery)))
        # Arrow
        ax = self.rect.right - 18
        ay = self.rect.centery
        arrow = [(ax, ay - 3), (ax + 8, ay - 3), (ax + 4, ay + 3)]
        if self.open:
            arrow = [(ax, ay + 3), (ax + 8, ay + 3), (ax + 4, ay - 3)]
        pygame.draw.polygon(surf, C_TEXT, arrow)

    def draw_list(self, surf: pygame.Surface, font: pygame.font.Font, mouse_pos):
        if not self.open:
            return
        # Draw shadow for dropdown list
        shadow_rect = pygame.Rect(self.rect.x + 4, self.rect.bottom + 4, self.rect.width, len(self.options) * self.item_h)
        s = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        s.fill((0, 0, 0, 100))
        surf.blit(s, shadow_rect)

        for i, opt in enumerate(self.options):
            r = pygame.Rect(self.rect.x,
                            self.rect.bottom + i * self.item_h,
                            self.rect.width, self.item_h)
            bg = C_BTN_ACTIVE if i == self.selected else (
                C_BTN_HOVER if r.collidepoint(mouse_pos) else C_BTN)
            pygame.draw.rect(surf, bg, r)
            pygame.draw.rect(surf, C_BTN_BORDER, r, 1)
            t = font.render(opt, True, C_TEXT)
            surf.blit(t, t.get_rect(midleft=(r.x + 10, r.centery)))

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """Returns True if selection changed."""
        if self.rect.collidepoint(pos):
            self.open = not self.open
            return False
        if self.open:
            for i, _ in enumerate(self.options):
                r = pygame.Rect(self.rect.x,
                                self.rect.bottom + i * self.item_h,
                                self.rect.width, self.item_h)
                if r.collidepoint(pos):
                    changed = self.selected != i
                    self.selected = i
                    self.open = False
                    return changed
            self.open = False
        return False

    def close(self):
        self.open = False


class Slider:
    def __init__(self, rect: pygame.Rect, min_val: int, max_val: int, value: int):
        self.rect    = rect
        self.min_val = min_val
        self.max_val = max_val
        self.value   = value
        self.dragging= False

    @property
    def knob_x(self) -> int:
        t = (self.value - self.min_val) / (self.max_val - self.min_val)
        return int(self.rect.x + t * self.rect.width)

    def draw(self, surf: pygame.Surface, font: pygame.font.Font):
        # Track background
        pygame.draw.rect(surf, C_BTN, self.rect, border_radius=10)
        # Filled part (glow)
        if self.value > self.min_val:
            filled = pygame.Rect(self.rect.x, self.rect.y,
                                 self.knob_x - self.rect.x, self.rect.height)
            pygame.draw.rect(surf, C_ACCENT, filled, border_radius=10)
            # Subtle glow
            glow_rect = filled.inflate(4, 4)
            s = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(s, (*C_ACCENT, 40), s.get_rect(), border_radius=10)
            surf.blit(s, glow_rect)

        # Knob
        pygame.draw.circle(surf, (255, 255, 255), (self.knob_x, self.rect.centery), 8)
        pygame.draw.circle(surf, C_ACCENT, (self.knob_x, self.rect.centery), 4)
        
        # Value label
        lbl = font.render(str(self.value), True, C_TEXT)
        surf.blit(lbl, (self.rect.right + 12, self.rect.y - 4))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            kx, ky = self.knob_x, self.rect.centery
            if abs(event.pos[0] - kx) < 12 and abs(event.pos[1] - ky) < 12:
                self.dragging = True
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            rel = (event.pos[0] - self.rect.x) / self.rect.width
            rel = max(0.0, min(1.0, rel))
            self.value = int(self.min_val + rel * (self.max_val - self.min_val))
            return True
        return False


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.W, self.H = screen.get_size()

        pygame.font.init()
        self.font_lg  = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_md  = pygame.font.SysFont("Segoe UI", 14)
        self.font_sm  = pygame.font.SysFont("Segoe UI", 12)
        self.font_xs  = pygame.font.SysFont("Segoe UI", 11)

        self.maze_surf: Optional[pygame.Surface] = None
        self.cell_px   = 24
        self.maze_origin = (PANEL_W + 10, 10)

    # ── Layout helpers ────────────────────────────────────────────────

    def compute_cell_size(self, maze: Maze):
        avail_w = self.W - PANEL_W - 20
        avail_h = self.H - 20
        ir, ic  = maze.internal_size()
        self.cell_px = max(MIN_CELL_PX,
                           min(MAX_CELL_PX,
                               min(avail_w // ic, avail_h // ir)))
        # Center maze in available space
        total_w = ic * self.cell_px
        total_h = ir * self.cell_px
        ox = PANEL_W + (avail_w - total_w) // 2 + 10
        oy = (avail_h - total_h) // 2 + 10
        self.maze_origin = (ox, oy)

    def logical_to_screen(self, r: int, c: int, maze: Maze) -> Tuple[int, int]:
        ir, ic = maze.cell_to_internal(r, c)
        ox, oy = self.maze_origin
        px = ox + ic * self.cell_px
        py = oy + ir * self.cell_px
        return px + self.cell_px // 2, py + self.cell_px // 2

    def get_interpolated_pos(self, prev: Tuple, curr: Tuple, t: float, maze: Maze) -> Tuple[int, int]:
        """Interpolate between two logical positions for smooth movement."""
        t = max(0.0, min(1.0, t))
        # Ease-out quad
        t = 1 - (1 - t) * (1 - t)
        
        p1 = self.logical_to_screen(*prev, maze)
        p2 = self.logical_to_screen(*curr, maze)
        
        x = p1[0] + (p2[0] - p1[0]) * t
        y = p1[1] + (p2[1] - p1[1]) * t
        return int(x), int(y)

    # ── Static maze surface ───────────────────────────────────────────

    def build_maze_surface(self, maze: Maze):
        ir, ic = maze.internal_size()
        w = ic * self.cell_px
        h = ir * self.cell_px
        surf = pygame.Surface((w, h))
        surf.fill(C_BG)
        for row in range(ir):
            for col in range(ic):
                color = C_WALL if maze.is_wall(row, col) else C_PATH
                rect  = pygame.Rect(col * self.cell_px, row * self.cell_px,
                                    self.cell_px, self.cell_px)
                pygame.draw.rect(surf, color, rect)
        self.maze_surf = surf

    # ── Main draw ─────────────────────────────────────────────────────

    def draw(self, maze: Maze, state: GameState,
             player_path: List[Tuple[int, int]],
             ui: "UIPanel"):
        self.screen.fill(C_BG)

        # ── Maze ──
        if self.maze_surf:
            self.screen.blit(self.maze_surf, self.maze_origin)

        # ── Persistent Overlay (Trails & Paths) ──
        if not hasattr(self, 'overlay_surf') or self.overlay_surf.get_size() != (self.W, self.H):
            self.overlay_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.overlay_surf.fill((0, 0, 0, 0))

        # ── Path overlay ──
        if player_path and len(player_path) > 1:
            points = [self.logical_to_screen(r, c, maze) for r, c in player_path]
            pygame.draw.lines(self.overlay_surf, C_PATH_HIGHLIGHT, False, points, max(2, self.cell_px // 4))
            for pt in points:
                pygame.draw.circle(self.screen, C_ACCENT, pt, max(1, self.cell_px // 10))

        # ── Trails ──
        self._draw_trail(maze, state.player_trail, C_PLAYER, alpha=50)
        self._draw_trail(maze, state.enemy_trail,  C_ENEMY,  alpha=50)
        
        self.screen.blit(self.overlay_surf, (0, 0))

        # ── Goal ──

        # ── Goal ──
        gx, gy = self.logical_to_screen(*state.goal, maze)
        self._draw_diamond(gx, gy, int(self.cell_px * 0.45), C_GOAL)

        # ── Start marker ──
        sx, sy = self.logical_to_screen(0, 0, maze)
        r = int(self.cell_px * AGENT_RADIUS)
        pygame.draw.rect(self.screen, C_START,
                         pygame.Rect(sx - r, sy - r, 2 * r, 2 * r), border_radius=3)

        # Calculate interpolation factor (assume 0.25s for move)
        t = state.move_timer / 0.25

        # ── Player ──
        px, py = self.get_interpolated_pos(state.prev_player_pos, state.player_pos, t, maze)
        self._draw_agent(px, py, C_PLAYER, "P")

        # ── Enemy ──
        ex, ey = self.get_interpolated_pos(state.prev_enemy_pos, state.enemy_pos, t, maze)
        self._draw_agent(ex, ey, C_ENEMY, "E")

        # ── Left panel ──
        ui.draw(self.screen)

        # ── Overlay on game over ──
        if state.is_over():
            self._draw_overlay(state)

        pygame.display.flip()

    def _draw_trail(self, maze: Maze, trail, color, alpha=60):
        if len(trail) < 2:
            return
        pts = [self.logical_to_screen(r, c, maze) for r, c in trail]
        pygame.draw.lines(self.overlay_surf, (*color, alpha), False, pts, max(2, self.cell_px // 10))

    def _draw_agent(self, x: int, y: int, color: Tuple, letter: str):
        r = int(self.cell_px * AGENT_RADIUS)
        # Glow
        for i in range(3, 0, -1):
            s = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, 20 // i), (r * 3, r * 3), r * (1 + i * 0.5))
            self.screen.blit(s, (x - r * 3, y - r * 3))
        
        # Body
        pygame.draw.circle(self.screen, color, (x, y), r)
        pygame.draw.circle(self.screen, (255, 255, 255), (x, y), r, 2)
        # Letter
        lbl = self.font_xs.render(letter, True, (0, 0, 0))
        self.screen.blit(lbl, lbl.get_rect(center=(x, y)))

    def _draw_diamond(self, x: int, y: int, size: int, color: Tuple):
        pts = [(x, y - size), (x + size, y), (x, y + size), (x - size, y)]
        pygame.draw.polygon(self.screen, color, pts)
        # Glow
        glow = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        pygame.draw.polygon(glow, (*color, 50),
                            [(size * 2, size), (size * 3, size * 2),
                             (size * 2, size * 3), (size, size * 2)])
        self.screen.blit(glow, (x - size * 2, y - size * 2))

    def _draw_overlay(self, state: GameState):
        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        # Deep blur/darken effect
        overlay.fill((5, 5, 10, 200))
        self.screen.blit(overlay, (0, 0))
        
        is_win = state.status == "win"
        is_ai  = state.mode == "ai"
        color  = C_WIN if is_win else C_LOSE
        
        if is_win:
            msg = "MISSION ACCOMPLISHED"
            sub = "The target has been reached successfully."
        else:
            msg = "SYSTEM OVERLOADED"
            sub = "The subject has been intercepted by the sentinel."
        
        # Glow for text
        big_font = pygame.font.SysFont("Segoe UI", 36, bold=True)
        small_font = self.font_md
        
        txt_main = big_font.render(msg, True, color)
        txt_sub  = small_font.render(sub, True, C_TEXT_DIM)
        txt_hint = self.font_sm.render("PRESS 'R' TO REINITIALIZE SYSTEM", True, C_ACCENT)
        
        cx, cy = self.W // 2, self.H // 2
        
        # Background box for text
        box_w, box_h = max(txt_main.get_width(), txt_sub.get_width()) + 100, 180
        box_rect = pygame.Rect(cx - box_w // 2, cy - box_h // 2, box_w, box_h)
        pygame.draw.rect(self.screen, C_PANEL, box_rect, border_radius=15)
        pygame.draw.rect(self.screen, color, box_rect, 2, border_radius=15)
        
        self.screen.blit(txt_main, txt_main.get_rect(center=(cx, cy - 30)))
        self.screen.blit(txt_sub,  txt_sub.get_rect(center=(cx, cy + 10)))
        self.screen.blit(txt_hint, txt_hint.get_rect(center=(cx, cy + 50)))


# ── UI Panel ──────────────────────────────────────────────────────────

class UIPanel:
    """Left-side control panel."""

    ALGO_OPTIONS = ["BFS", "DFS", "A* (Manhattan)", "Alpha-Beta (Enemy)"]
    MODE_OPTIONS = ["AI Player", "Human Player"]

    def __init__(self, h: int):
        self.H = h
        self._build_fonts()
        self._build_widgets()

    def _build_fonts(self):
        self.font_title = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.font_label = pygame.font.SysFont("Segoe UI", 13)
        self.font_val   = pygame.font.SysFont("Segoe UI", 13, bold=True)

    def _build_widgets(self):
        x = 14
        W = PANEL_W - 28

        self.algo_dd   = Dropdown(pygame.Rect(x, 90, W, 30),
                                  self.ALGO_OPTIONS, selected=2)
        self.mode_dd   = Dropdown(pygame.Rect(x, 155, W, 30),
                                  self.MODE_OPTIONS, selected=0)
        self.size_slider = Slider(pygame.Rect(x, 220, W - 30, 14),
                                  min_val=5, max_val=25, value=10)

        btn_y  = 260
        btn_h  = 32
        gap    = 8
        self.btn_start  = Button(pygame.Rect(x, btn_y,        W, btn_h), "Start / Restart", "start")
        self.btn_step   = Button(pygame.Rect(x, btn_y + btn_h + gap, W, btn_h), "Step (Space)",    "step")
        self.btn_regen  = Button(pygame.Rect(x, btn_y + 2*(btn_h+gap), W, btn_h), "New Maze",        "regen")
        self.btn_auto   = Button(pygame.Rect(x, btn_y + 3*(btn_h+gap), W, btn_h), "Auto-Run",        "auto")
        self.buttons    = [self.btn_start, self.btn_step, self.btn_regen, self.btn_auto]

        # Metrics placeholders
        self.metrics_y  = btn_y + 4 * (btn_h + gap) + 16

    @property
    def selected_algo(self) -> str:
        return self.ALGO_OPTIONS[self.algo_dd.selected]

    @property
    def selected_mode(self) -> str:
        return self.MODE_OPTIONS[self.mode_dd.selected]

    @property
    def maze_size(self) -> int:
        return self.size_slider.value

    def draw(self, surf: pygame.Surface):
        # Panel background
        panel_rect = pygame.Rect(0, 0, PANEL_W, self.H)
        pygame.draw.rect(surf, C_PANEL, panel_rect)
        pygame.draw.rect(surf, C_PANEL_BORDER, panel_rect, 1)

        # Title
        title = self.font_title.render("Hybrid Maze AI", True, C_ACCENT)
        surf.blit(title, title.get_rect(centerx=PANEL_W // 2, y=14))
        sub = self.font_label.render("Search Algorithm Visualiser", True, C_TEXT_DIM)
        surf.blit(sub, sub.get_rect(centerx=PANEL_W // 2, y=34))

        # Divider
        pygame.draw.line(surf, C_PANEL_BORDER, (10, 55), (PANEL_W - 10, 55))

        # Labels
        self._lbl(surf, "Player Algorithm:", 14, 68)
        self._lbl(surf, "Player Mode:", 14, 134)
        self._lbl(surf, f"Maze Size ({self.maze_size}x{self.maze_size}):", 14, 200)

        # Widgets
        mouse = pygame.mouse.get_pos()
        self.algo_dd.draw(surf, self.font_label, mouse)
        self.mode_dd.draw(surf, self.font_label, mouse)
        self.size_slider.draw(surf, self.font_label)

        for btn in self.buttons:
            btn.check_hover(mouse)
            btn.draw(surf, self.font_label)

        # Draw open dropdown lists last so they appear on top
        self.algo_dd.draw_list(surf, self.font_label, mouse)
        self.mode_dd.draw_list(surf, self.font_label, mouse)

        # Divider
        pygame.draw.line(surf, C_PANEL_BORDER, (10, self.metrics_y - 6),
                         (PANEL_W - 10, self.metrics_y - 6))

    def draw_metrics(self, surf: pygame.Surface,
                     p_algo: str, p_nodes: int, p_len: int, p_ms: float,
                     e_nodes: int):
        y = self.metrics_y
        self._lbl(surf, "Player Metrics", 14, y, color=C_ACCENT)
        y += 20
        self._metric(surf, "Algorithm",  p_algo,          y); y += 18
        self._metric(surf, "Nodes explored", str(p_nodes), y); y += 18
        self._metric(surf, "Path length",    str(p_len),   y); y += 18
        self._metric(surf, "Time (ms)",  f"{p_ms:.2f}",    y); y += 26

        self._lbl(surf, "Enemy (Alpha-Beta)", 14, y, color=C_ENEMY)
        y += 20
        self._metric(surf, "Nodes explored", str(e_nodes), y); y += 18

        # Legend
        y += 12
        self._legend(surf, C_PLAYER, "Player (P)", 14, y); y += 20
        self._legend(surf, C_ENEMY,  "Enemy  (E)", 14, y); y += 20
        self._legend(surf, C_GOAL,   "Goal   (◆)", 14, y)

    def _lbl(self, surf, text, x, y, color=C_TEXT_DIM):
        t = self.font_label.render(text, True, color)
        surf.blit(t, (x, y))

    def _metric(self, surf, label, value, y):
        lbl = self.font_label.render(label + ":", True, C_TEXT_DIM)
        val = self.font_val.render(value, True, C_TEXT)
        surf.blit(lbl, (14, y))
        surf.blit(val, (PANEL_W - 14 - val.get_width(), y))

    def _legend(self, surf, color, text, x, y):
        pygame.draw.circle(surf, color, (x + 7, y + 7), 6)
        t = self.font_label.render(text, True, C_TEXT_DIM)
        surf.blit(t, (x + 18, y))

    def handle_event(self, event: pygame.event.Event):
        """Returns list of tags of triggered buttons."""
        triggered = []
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if not self.algo_dd.handle_click(pos):
                self.mode_dd.handle_click(pos)
            for btn in self.buttons:
                if btn.clicked(pos):
                    triggered.append(btn.tag)
        self.size_slider.handle_event(event)
        return triggered