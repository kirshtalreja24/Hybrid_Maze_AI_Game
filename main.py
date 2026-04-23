import sys
import time
import random
import pygame
from maze import Maze
from algorithm import run_algorithm, AlphaBetaEnemy
from game_state import GameState
from renderer import Renderer, UIPanel, PANEL_W

WIN_W, WIN_H = 1100, 720
FPS = 60
AUTO_DELAY = 0.18

def make_enemy_start(maze):
    walkable = [(r, c) for r in range(maze.rows) for c in range(maze.cols) 
                if (r, c) != (0, 0) and (r, c) != maze.goal]
    far_enough = [p for p in walkable if (p[0] + p[1]) > 5]
    return random.choice(far_enough) if far_enough else random.choice(walkable or [(maze.rows-1, 0)])

def init_game(maze, ui):
    mode = "ai" if ui.selected_mode == "AI Player" else "human"
    algo = ui.selected_algo
    state = GameState((0, 0), make_enemy_start(maze), maze.goal, mode=mode)
    if mode == "ai":
        path, nodes, ms = run_algorithm(algo, (0, 0), maze.goal, maze.get_neighbors, state.enemy_pos)
        state.set_player_path(path, nodes, ms, algo)
    return state

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Hybrid Maze AI — Search Algorithm Visualiser")
    clock, ui, renderer = pygame.time.Clock(), UIPanel(WIN_H), Renderer(screen)
    maze = Maze(ui.maze_size, ui.maze_size)
    renderer.compute_cell_size(maze)
    renderer.build_maze_surface(maze)
    state = init_game(maze, ui)
    enemy_ai = AlphaBetaEnemy(depth=4)
    auto_run, started, last_step = False, False, 0.0
    def restart():
        nonlocal state, started
        state, started = init_game(maze, ui), True
    def regen_maze():
        nonlocal maze, state, auto_run, started
        maze = Maze(ui.maze_size, ui.maze_size)
        renderer.compute_cell_size(maze)
        renderer.build_maze_surface(maze)
        auto_run, started = False, False
        restart()
    running = True
    while running:
        dt = clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                if event.key == pygame.K_r: restart()
                if event.key == pygame.K_SPACE and started: state.step(maze, ui.selected_algo, enemy_ai)
                if started and state.mode == "human" and not state.is_over():
                    moves = {pygame.K_UP:(-1,0), pygame.K_DOWN:(1,0), pygame.K_LEFT:(0,-1), pygame.K_RIGHT:(0,1),
                             pygame.K_w:(-1,0), pygame.K_s:(1,0), pygame.K_a:(0,-1), pygame.K_d:(0,1)}
                    if event.key in moves:
                        nr, nc = state.player_pos[0]+moves[event.key][0], state.player_pos[1]+moves[event.key][1]
                        if (nr, nc) in maze.get_neighbors(*state.player_pos):
                            state.human_step((nr, nc), maze, enemy_ai)
            for tag in ui.handle_event(event):
                if tag == "start": restart()
                elif tag == "step" and started: state.step(maze, ui.selected_algo, enemy_ai)
                elif tag == "regen": regen_maze()
                elif tag == "auto":
                    auto_run = not auto_run
                    ui.btn_auto.active = auto_run
        if not started and ui.maze_size != maze.rows:
            regen_maze()
            started = False
        state.move_timer += dt / 1000.0
        if auto_run and started and not state.is_over() and state.mode == "ai":
            if time.time() - last_step >= AUTO_DELAY:
                state.step(maze, ui.selected_algo, enemy_ai)
                last_step = time.time()
        renderer.draw(maze, state, state.player_path if started else [], ui)
        ui.draw_metrics(screen, state.player_metrics.algorithm, state.player_metrics.nodes_explored, 
                        state.player_metrics.path_length, state.player_metrics.exec_time_ms, 
                        state.enemy_metrics.nodes_explored)
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()