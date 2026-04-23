"""
main.py — Entry point for the Hybrid Maze AI Game.

Controls:
  ▶ Start / Restart  — Compute path & begin game
  ⏭ Step (Space)     — Advance one move at a time
  ⚡ Auto-Run         — Animate moves automatically
  🔀 New Maze         — Regenerate with random seed
  Arrow keys          — Move player manually (Human mode)
  R                   — Restart current maze
  ESC                 — Quit
"""

import sys
import time
import random
import pygame

from maze import Maze
from algorithm import run_algorithm, AlphaBetaEnemy, ALGORITHM_NAMES
from game_state import GameState
from renderer import Renderer, UIPanel, PANEL_W


# ── Constants ────────────────────────────────────────────────────────
WIN_W      = 1100
WIN_H      = 720
FPS        = 60
AUTO_DELAY = 0.18   # seconds between auto-steps


def make_enemy_start(maze: Maze) -> tuple:
    """Pick a random walkable cell that is far from the player (0,0)."""
    walkable = []
    for r in range(maze.rows):
        for c in range(maze.cols):
            # Check if logical cell is reachable (not surrounded by walls)
            # and not the start (0,0) or goal
            if (r, c) != (0, 0) and (r, c) != (maze.rows-1, maze.cols-1):
                # We can just pick any cell that is on a path
                walkable.append((r, c))
    
    if not walkable:
        return (maze.rows - 1, 0)
    
    # Filter for cells that are at least 5 units away from start if possible
    far_enough = [p for p in walkable if (p[0] + p[1]) > 5]
    if far_enough:
        return random.choice(far_enough)
    
    return random.choice(walkable)


def init_game(maze: Maze, algo: str, mode: str) -> GameState:
    player_start = (0, 0)
    enemy_start  = make_enemy_start(maze)
    state = GameState(player_start, enemy_start, maze.goal, mode=mode)

    if mode == "ai":
        # For A* Smart, we still want an initial path to show something
        path, nodes, ms = run_algorithm(algo, player_start, maze.goal,
                                        maze.get_neighbors, enemy_start)
        state.set_player_path(path, nodes, ms, algo)
    else:
        # Human mode — no pre-computed path
        state.set_player_path([], 0, 0.0, "Human")
    return state


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Hybrid Maze AI — Search Algorithm Visualiser")
    clock  = pygame.time.Clock()

    ui       = UIPanel(WIN_H)
    renderer = Renderer(screen)

    # Initial maze
    maze_size = ui.maze_size
    maze      = Maze(maze_size, maze_size)
    renderer.compute_cell_size(maze)
    renderer.build_maze_surface(maze)

    algo  = ui.selected_algo
    mode  = "ai" if ui.selected_mode == "AI Player" else "human"
    state = init_game(maze, algo, mode)

    enemy_ai    = AlphaBetaEnemy(depth=4)
    auto_run    = False
    last_step   = 0.0
    started     = False   # whether player has pressed Start

    def restart():
        nonlocal state, auto_run, started, algo, mode
        algo  = ui.selected_algo if ui.selected_algo != "Alpha-Beta (Enemy)" else "A* (Manhattan)"
        mode  = "ai" if ui.selected_mode == "AI Player" else "human"
        state = init_game(maze, algo, mode)
        started = True

    def regen_maze():
        nonlocal maze, state, auto_run, started
        sz   = ui.maze_size
        maze = Maze(sz, sz)
        renderer.compute_cell_size(maze)
        renderer.build_maze_surface(maze)
        auto_run = False
        started  = False
        restart()

    def do_step():
        """Advance one full turn (player move + enemy response)."""
        if state.is_over():
            return

        # ── Player turn ──
        if mode == "ai":
            # If Smart A*, recalculate path every step
            if ui.selected_algo == "A* Smart (Avoid Enemy)":
                path, nodes, ms = run_algorithm(ui.selected_algo, state.player_pos, maze.goal,
                                                maze.get_neighbors, state.enemy_pos)
                if len(path) > 1:
                    state.move_player(path[1])
                    state.player_metrics.nodes_explored = nodes
                    state.player_metrics.path_length = len(path)
                    state.player_metrics.exec_time_ms = ms
            else:
                state.advance_player_ai()
        # Human: movement handled by key events directly

        if state.is_over():
            return

        # ── Enemy turn (Alpha-Beta) ──
        next_pos = enemy_ai.best_move(state.enemy_pos,
                                       state.player_pos,
                                       state.goal,
                                       maze.get_neighbors)
        if next_pos:
            state.move_enemy(next_pos)
        state.set_enemy_metrics(enemy_ai.nodes_explored)

    # ─────────────────────────────────────────────────────────────────
    # Main loop
    # ─────────────────────────────────────────────────────────────────
    running = True
    while running:
        dt = clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        # ── Events ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    restart()
                if event.key == pygame.K_SPACE and started:
                    do_step()
                # Human player movement
                if started and mode == "human" and not state.is_over():
                    direction_map = {
                        pygame.K_UP:    (-1, 0),
                        pygame.K_DOWN:  ( 1, 0),
                        pygame.K_LEFT:  ( 0,-1),
                        pygame.K_RIGHT: ( 0, 1),
                        pygame.K_w:     (-1, 0),
                        pygame.K_s:     ( 1, 0),
                        pygame.K_a:     ( 0,-1),
                        pygame.K_d:     ( 0, 1),
                    }
                    if event.key in direction_map:
                        dr, dc = direction_map[event.key]
                        nr = state.player_pos[0] + dr
                        nc = state.player_pos[1] + dc
                        neighbors = maze.get_neighbors(*state.player_pos)
                        if (nr, nc) in neighbors:
                            state.move_player((nr, nc))
                            # Enemy responds immediately
                            if not state.is_over():
                                next_pos = enemy_ai.best_move(
                                    state.enemy_pos, state.player_pos,
                                    state.goal,
                                    maze.get_neighbors)
                                if next_pos:
                                    state.move_enemy(next_pos)
                                state.set_enemy_metrics(enemy_ai.nodes_explored)

            # UI buttons
            triggered = ui.handle_event(event)
            for tag in triggered:
                if tag == "start":
                    restart()
                elif tag == "step" and started:
                    do_step()
                elif tag == "regen":
                    regen_maze()
                elif tag == "auto":
                    auto_run = not auto_run
                    ui.btn_auto.active = auto_run

            # Slider change → rebuild maze on size change
            if event.type == pygame.MOUSEMOTION:
                pass   # handled next frame

        # Rebuild maze if size slider changed
        if not started and ui.maze_size != maze.rows:
            sz   = ui.maze_size
            maze = Maze(sz, sz)
            renderer.compute_cell_size(maze)
            renderer.build_maze_surface(maze)

        # ── Update timers ──
        state.move_timer += dt / 1000.0

        # ── Auto-run ──
        now = time.time()
        if auto_run and started and not state.is_over() and mode == "ai":
            if now - last_step >= AUTO_DELAY:
                do_step()
                last_step = now

        # ── Draw ──
        p_path = state.player_path if started else []
        renderer.draw(maze, state, p_path, ui)

        # Draw metrics on top of panel
        ui.draw_metrics(
            screen,
            p_algo  = state.player_metrics.algorithm,
            p_nodes = state.player_metrics.nodes_explored,
            p_len   = state.player_metrics.path_length,
            p_ms    = state.player_metrics.exec_time_ms,
            e_nodes = state.enemy_metrics.nodes_explored,
        )

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()