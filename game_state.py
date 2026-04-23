"""
game_state.py — Tracks game state, turn management, metrics, and win/loss logic.
"""

from typing import Tuple, List, Optional
from dataclasses import dataclass

@dataclass
class Metrics:
    nodes_explored: int = 0
    path_length: int = 0
    exec_time_ms: float = 0.0
    algorithm: str = ""

class GameState:
    """
    Turn-based game state manager.
    Modes: 'human' | 'ai'
    """
    STATUS_PLAYING = "playing"
    STATUS_WIN     = "win"
    STATUS_LOSE    = "lose"

    def __init__(self, player_start: Tuple, enemy_start: Tuple, goal: Tuple, mode: str = "ai"):
        self.player_pos = player_start
        self.enemy_pos  = enemy_start
        self.goal       = goal
        self.mode       = mode
        self.status     = self.STATUS_PLAYING

        self.player_path = []
        self.player_step = 0
        self.player_metrics = Metrics()
        self.enemy_metrics  = Metrics()

        self.player_trail = [player_start]
        self.enemy_trail  = [enemy_start]

        self.prev_player_pos = player_start
        self.prev_enemy_pos  = enemy_start
        self.move_timer      = 0.0

    def is_over(self) -> bool:
        return self.status != self.STATUS_PLAYING

    def move_agent(self, agent: str, new_pos: Tuple):
        """Generic movement for both player and enemy."""
        if self.is_over(): return

        if agent == "player":
            self.prev_player_pos = self.player_pos
            self.player_pos = new_pos
            self.player_trail.append(new_pos)
        else:
            self.prev_enemy_pos = self.enemy_pos
            self.enemy_pos = new_pos
            self.enemy_trail.append(new_pos)

        self.move_timer = 0.0
        
        # Check Win/Loss
        if self.player_pos == self.goal:
            self.status = self.STATUS_WIN
        elif self.player_pos == self.enemy_pos:
            self.status = self.STATUS_LOSE

    def human_step(self, new_pos: Tuple, maze, enemy_ai):
        """Handle manual player move and immediate enemy response."""
        if self.is_over(): return
        self.move_agent("player", new_pos)
        if not self.is_over():
            next_pos = enemy_ai.best_move(self.enemy_pos, self.player_pos, self.goal, maze.get_neighbors)
            if next_pos:
                self.move_agent("enemy", next_pos)
            self.enemy_metrics.nodes_explored = enemy_ai.nodes_explored

    def step(self, maze, algo_name: str, enemy_ai):
        """Advance one turn: player moves, then enemy responds."""
        if self.is_over(): return

        # 1. Player Turn
        if self.mode == "ai":
            if "Smart" in algo_name:
                from algorithm import run_algorithm
                path, nodes, ms = run_algorithm(algo_name, self.player_pos, self.goal, 
                                                maze.get_neighbors, self.enemy_pos)
                if len(path) > 1:
                    self.move_agent("player", path[1])
                    self.player_metrics.nodes_explored = nodes
                    self.player_metrics.path_length = len(path)
                    self.player_metrics.exec_time_ms = ms
            else:
                if self.player_step + 1 < len(self.player_path):
                    self.player_step += 1
                    self.move_agent("player", self.player_path[self.player_step])
        
        if self.is_over(): return

        # 2. Enemy Turn
        next_pos = enemy_ai.best_move(self.enemy_pos, self.player_pos, self.goal, maze.get_neighbors)
        if next_pos:
            self.move_agent("enemy", next_pos)
        self.enemy_metrics.nodes_explored = enemy_ai.nodes_explored

    def set_player_path(self, path: List[Tuple], nodes: int, ms: float, algo: str):
        self.player_path = path
        self.player_step = 0
        self.player_metrics.nodes_explored = nodes
        self.player_metrics.path_length    = len(path)
        self.player_metrics.exec_time_ms   = ms
        self.player_metrics.algorithm      = algo