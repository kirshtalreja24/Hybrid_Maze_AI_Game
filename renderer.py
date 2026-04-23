import pygame
from maze import Maze
from game_state import GameState

C_BG, C_WALL, C_PATH = (15, 17, 26), (32, 36, 52), (22, 25, 38)
C_PANEL, C_PANEL_BORDER = (20, 24, 36), (50, 60, 90)
C_PLAYER, C_ENEMY, C_GOAL, C_START = (80, 220, 150), (240, 90, 110), (80, 180, 240), (140, 120, 255)
C_PATH_HIGHLIGHT = (80, 180, 240, 80)
C_TEXT, C_TEXT_DIM, C_ACCENT = (220, 225, 245), (130, 135, 160), (80, 180, 240)
C_WIN, C_LOSE = (80, 220, 150), (240, 90, 110)
C_BTN, C_BTN_HOVER, C_BTN_ACTIVE = (40, 46, 68), (55, 62, 90), (80, 180, 240)
C_BTN_TEXT, C_BTN_BORDER = (230, 235, 255), (65, 75, 110)
PANEL_W, MIN_CELL_PX, MAX_CELL_PX, AGENT_RADIUS = 260, 12, 48, 0.38

class Button:
    def __init__(self, rect, label, tag=""):
        self.rect, self.label, self.tag, self.hovered, self.active = rect, label, tag, False, False
    def draw(self, surf, font):
        col = C_BTN_ACTIVE if self.active else (C_BTN_HOVER if self.hovered else C_BTN)
        pygame.draw.rect(surf, col, self.rect, border_radius=8)
        b_col = C_ACCENT if (self.hovered or self.active) else C_BTN_BORDER
        pygame.draw.rect(surf, b_col, self.rect, 1, border_radius=8)
        txt = font.render(self.label, True, C_BTN_TEXT)
        surf.blit(txt, txt.get_rect(center=self.rect.center))
    def check_hover(self, pos): self.hovered = self.rect.collidepoint(pos)
    def clicked(self, pos): return self.rect.collidepoint(pos)

class Dropdown:
    def __init__(self, rect, options, selected=0):
        self.rect, self.options, self.selected, self.open, self.item_h = rect, options, selected, False, rect.height
    def draw(self, surf, font, mouse_pos):
        col = C_BTN_HOVER if self.rect.collidepoint(mouse_pos) else C_BTN
        pygame.draw.rect(surf, col, self.rect, border_radius=6)
        pygame.draw.rect(surf, C_BTN_BORDER, self.rect, 1, border_radius=6)
        label = font.render(self.options[self.selected], True, C_TEXT)
        surf.blit(label, (self.rect.x + 10, self.rect.y + 7))
        pygame.draw.polygon(surf, C_TEXT, [(self.rect.right - 18, self.rect.centery + (3 if self.open else -3)), 
                                           (self.rect.right - 10, self.rect.centery + (3 if self.open else -3)), 
                                           (self.rect.right - 14, self.rect.centery + (-3 if self.open else 3))])
    def draw_list(self, surf, font, mouse_pos):
        if not self.open: return
        for i, opt in enumerate(self.options):
            r = pygame.Rect(self.rect.x, self.rect.bottom + i * self.item_h, self.rect.width, self.item_h)
            bg = C_BTN_ACTIVE if i == self.selected else (C_BTN_HOVER if r.collidepoint(mouse_pos) else C_BTN)
            pygame.draw.rect(surf, bg, r)
            pygame.draw.rect(surf, C_BTN_BORDER, r, 1)
            t = font.render(opt, True, C_TEXT)
            surf.blit(t, (r.x + 10, r.y + 7))
    def handle_click(self, pos):
        if self.rect.collidepoint(pos): self.open = not self.open; return False
        if self.open:
            for i in range(len(self.options)):
                if pygame.Rect(self.rect.x, self.rect.bottom + i * self.item_h, self.rect.width, self.item_h).collidepoint(pos):
                    self.selected, self.open = i, False; return True
            self.open = False
        return False

class Slider:
    def __init__(self, rect, min_val, max_val, value):
        self.rect, self.min_val, self.max_val, self.value, self.dragging = rect, min_val, max_val, value, False
    def draw(self, surf, font):
        pygame.draw.rect(surf, C_BTN, self.rect, border_radius=10)
        t = (self.value - self.min_val) / (self.max_val - self.min_val)
        kx = int(self.rect.x + t * self.rect.width)
        if self.value > self.min_val:
            pygame.draw.rect(surf, C_ACCENT, (self.rect.x, self.rect.y, kx - self.rect.x, self.rect.height), border_radius=10)
        pygame.draw.circle(surf, (255, 255, 255), (kx, self.rect.centery), 8)
        pygame.draw.circle(surf, C_ACCENT, (kx, self.rect.centery), 4)
        lbl = font.render(str(self.value), True, C_TEXT)
        surf.blit(lbl, (self.rect.right + 12, self.rect.y - 4))
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            t = (self.value - self.min_val) / (self.max_val - self.min_val)
            if abs(event.pos[0] - int(self.rect.x + t * self.rect.width)) < 15: self.dragging = True
        if event.type == pygame.MOUSEBUTTONUP: self.dragging = False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            rel = max(0.0, min(1.0, (event.pos[0] - self.rect.x) / self.rect.width))
            self.value = int(self.min_val + rel * (self.max_val - self.min_val)); return True
        return False

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.W, self.H = screen.get_size()
        pygame.font.init()
        self.font_md = pygame.font.SysFont("Segoe UI", 14)
        self.font_sm = pygame.font.SysFont("Segoe UI", 12)
        self.font_xs = pygame.font.SysFont("Segoe UI", 11)
        self.maze_surf, self.cell_px, self.maze_origin = None, 24, (PANEL_W + 10, 10)
    def compute_cell_size(self, maze):
        avail_w, avail_h = self.W - PANEL_W - 20, self.H - 20
        ir, ic = maze.internal_size()
        self.cell_px = max(MIN_CELL_PX, min(MAX_CELL_PX, min(avail_w // ic, avail_h // ir)))
        self.maze_origin = (PANEL_W + (avail_w - ic * self.cell_px) // 2 + 10, (avail_h - ir * self.cell_px) // 2 + 10)
    def logical_to_screen(self, r, c, maze):
        ir, ic = maze.cell_to_internal(r, c)
        return self.maze_origin[0] + ic * self.cell_px + self.cell_px // 2, self.maze_origin[1] + ir * self.cell_px + self.cell_px // 2
    def build_maze_surface(self, maze):
        ir, ic = maze.internal_size()
        surf = pygame.Surface((ic * self.cell_px, ir * self.cell_px))
        for r in range(ir):
            for c in range(ic):
                pygame.draw.rect(surf, C_WALL if maze.is_wall(r, c) else C_PATH, (c * self.cell_px, r * self.cell_px, self.cell_px, self.cell_px))
        self.maze_surf = surf
    def draw(self, maze, state, player_path, ui):
        self.screen.fill(C_BG)
        if self.maze_surf: self.screen.blit(self.maze_surf, self.maze_origin)
        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        if player_path and len(player_path) > 1:
            pts = [self.logical_to_screen(r, c, maze) for r, c in player_path]
            pygame.draw.lines(overlay, C_PATH_HIGHLIGHT, False, pts, max(2, self.cell_px // 4))
        for trail, col in [(state.player_trail, C_PLAYER), (state.enemy_trail, C_ENEMY)]:
            if len(trail) > 1:
                pts = [self.logical_to_screen(r, c, maze) for r, c in trail]
                pygame.draw.lines(overlay, (*col, 50), False, pts, max(2, self.cell_px // 10))
        self.screen.blit(overlay, (0, 0))
        gx, gy = self.logical_to_screen(*state.goal, maze)
        pygame.draw.polygon(self.screen, C_GOAL, [(gx, gy - 10), (gx + 10, gy), (gx, gy + 10), (gx - 10, gy)])
        sx, sy = self.logical_to_screen(0, 0, maze)
        r = int(self.cell_px * AGENT_RADIUS)
        pygame.draw.rect(self.screen, C_START, (sx - r, sy - r, 2 * r, 2 * r), border_radius=3)
        t = min(1.0, state.move_timer / 0.25)
        t = 1 - (1 - t) ** 2
        for pos, prev, col, label in [(state.player_pos, state.prev_player_pos, C_PLAYER, "P"), 
                                      (state.enemy_pos, state.prev_enemy_pos, C_ENEMY, "E")]:
            p1, p2 = self.logical_to_screen(*prev, maze), self.logical_to_screen(*pos, maze)
            x, y = p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t
            pygame.draw.circle(self.screen, col, (int(x), int(y)), r)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(x), int(y)), r, 2)
            txt = self.font_xs.render(label, True, (0, 0, 0))
            self.screen.blit(txt, txt.get_rect(center=(int(x), int(y))))
        ui.draw(self.screen)
        if state.is_over(): self._draw_overlay(state)
    def _draw_overlay(self, state):
        s = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        s.fill((5, 5, 10, 200))
        self.screen.blit(s, (0, 0))
        is_win = state.status == "win"
        col = C_WIN if is_win else C_LOSE
        msg = "MISSION ACCOMPLISHED" if is_win else "SYSTEM OVERLOADED"
        box = pygame.Rect(self.W // 2 - 200, self.H // 2 - 50, 400, 100)
        pygame.draw.rect(self.screen, C_PANEL, box, border_radius=15)
        pygame.draw.rect(self.screen, col, box, 2, border_radius=15)
        txt = pygame.font.SysFont("Segoe UI", 28, bold=True).render(msg, True, col)
        self.screen.blit(txt, txt.get_rect(center=(self.W // 2, self.H // 2 - 10)))
        hint = self.font_sm.render("PRESS 'R' TO RESTART", True, C_ACCENT)
        self.screen.blit(hint, hint.get_rect(center=(self.W // 2, self.H // 2 + 25)))

class UIPanel:
    ALGO_OPTIONS = ["BFS", "DFS", "A* (Manhattan)", "A* Smart (Avoid Enemy)"]
    MODE_OPTIONS = ["AI Player", "Human Player"]
    def __init__(self, h):
        self.H, self.font_title = h, pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.font_lbl = pygame.font.SysFont("Segoe UI", 13)
        self.font_val = pygame.font.SysFont("Segoe UI", 13, bold=True)
        x, W = 14, PANEL_W - 28
        self.algo_dd = Dropdown(pygame.Rect(x, 90, W, 30), self.ALGO_OPTIONS, 2)
        self.mode_dd = Dropdown(pygame.Rect(x, 155, W, 30), self.MODE_OPTIONS, 0)
        self.size_slider = Slider(pygame.Rect(x, 220, W - 30, 14), 5, 25, 10)
        self.buttons = [Button(pygame.Rect(x, 260 + i*40, W, 32), label, tag) for i, (label, tag) in enumerate([("Start / Restart", "start"), ("Step (Space)", "step"), ("New Maze", "regen"), ("Auto-Run", "auto")])]
        self.btn_auto = self.buttons[3]
    @property
    def selected_algo(self): return self.ALGO_OPTIONS[self.algo_dd.selected]
    @property
    def selected_mode(self): return self.MODE_OPTIONS[self.mode_dd.selected]
    @property
    def maze_size(self): return self.size_slider.value
    def draw(self, surf):
        pygame.draw.rect(surf, C_PANEL, (0, 0, PANEL_W, self.H))
        pygame.draw.rect(surf, C_PANEL_BORDER, (0, 0, PANEL_W, self.H), 1)
        surf.blit(self.font_title.render("Hybrid Maze AI", True, C_ACCENT), (PANEL_W//2 - 50, 14))
        mouse = pygame.mouse.get_pos()
        self.algo_dd.draw(surf, self.font_lbl, mouse)
        self.mode_dd.draw(surf, self.font_lbl, mouse)
        self.size_slider.draw(surf, self.font_lbl)
        for b in self.buttons: b.check_hover(mouse); b.draw(surf, self.font_lbl)
        self.algo_dd.draw_list(surf, self.font_lbl, mouse)
        self.mode_dd.draw_list(surf, self.font_lbl, mouse)
    def draw_metrics(self, surf, p_algo, p_nodes, p_len, p_ms, e_nodes):
        y = 430
        for label, val, col in [("Algorithm", p_algo, C_TEXT), ("Nodes Explored", str(p_nodes), C_TEXT), ("Path Length", str(p_len), C_TEXT), ("Time (ms)", f"{p_ms:.2f}", C_TEXT)]:
            surf.blit(self.font_lbl.render(label + ":", True, C_TEXT_DIM), (14, y))
            v = self.font_val.render(val, True, col)
            surf.blit(v, (PANEL_W - 14 - v.get_width(), y)); y += 20
        surf.blit(self.font_lbl.render("Enemy Explored:", True, C_ENEMY), (14, y+10))
        v = self.font_val.render(str(e_nodes), True, C_ENEMY)
        surf.blit(v, (PANEL_W - 14 - v.get_width(), y+10))
    def handle_event(self, event):
        triggered = []
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.algo_dd.handle_click(event.pos): self.mode_dd.handle_click(event.pos)
            for b in self.buttons:
                if b.clicked(event.pos): triggered.append(b.tag)
        self.size_slider.handle_event(event)
        return triggered