"""
game_state.py — Tracks game state, turn management, metrics, and win/loss logic.
"""

from typing import Tuple, List, Optional
from dataclasses import dataclass, field
import time


@dataclass
class Metrics:
    nodes_explored: int = 0
    path_length: int = 0
    exec_time_ms: float = 0.0
    algorithm: str = ""

    def reset(self):
        self.nodes_explored = 0
        self.path_length = 0
        self.exec_time_ms = 0.0


class GameState:
    """
    Turn-based game: Player moves first, then Enemy responds.

    Modes:
        'human'  — keyboard-controlled player
        'ai'     — player auto-follows chosen algorithm path
    """

    STATUS_PLAYING  = "playing"
    STATUS_WIN      = "win"
    STATUS_LOSE     = "lose"

    def __init__(self,
                 player_start: Tuple[int, int],
                 enemy_start: Tuple[int, int],
                 goal: Tuple[int, int],
                 mode: str = "ai"):
        self.player_pos   = player_start
        self.enemy_pos    = enemy_start
        self.goal         = goal
        self.mode         = mode          # 'human' | 'ai'
        self.status       = self.STATUS_PLAYING

        # Path followed by AI-controlled player
        self.player_path: List[Tuple[int, int]] = []
        self.player_step  = 0             # index into player_path

        # Metrics
        self.player_metrics = Metrics()
        self.enemy_metrics  = Metrics()

        # History for trail visualisation
        self.player_trail: List[Tuple[int, int]] = [player_start]
        self.enemy_trail:  List[Tuple[int, int]] = [enemy_start]

        # For interpolation
        self.prev_player_pos = player_start
        self.prev_enemy_pos  = enemy_start
        self.move_timer      = 0.0  # time since last move

        # Turn tracking
        self.turn: int = 0               # 0 = player's turn, 1 = enemy's turn
        self.moves: int = 0

    # ── State checks ──────────────────────────────────────────────────

    def check_status(self):
        if self.player_pos == self.goal:
            self.status = self.STATUS_WIN
        elif self.player_pos == self.enemy_pos:
            self.status = self.STATUS_LOSE

    def is_over(self) -> bool:
        return self.status != self.STATUS_PLAYING

    # ── Player movement ───────────────────────────────────────────────

    def move_player(self, new_pos: Tuple[int, int]):
        self.prev_player_pos = self.player_pos
        self.player_pos = new_pos
        self.player_trail.append(new_pos)
        self.moves += 1
        self.check_status()
        self.turn = 1   # now enemy's turn
        self.move_timer = 0.0

    def advance_player_ai(self) -> bool:
        """Advance player one step along pre-computed path. Returns True if moved."""
        if self.is_over():
            return False
        if self.player_step + 1 < len(self.player_path):
            self.player_step += 1
            self.move_player(self.player_path[self.player_step])
            return True
        return False

    # ── Enemy movement ────────────────────────────────────────────────

    def move_enemy(self, new_pos: Tuple[int, int]):
        if self.is_over():
            return
        self.prev_enemy_pos = self.enemy_pos
        self.enemy_pos = new_pos
        self.enemy_trail.append(new_pos)
        self.check_status()
        self.turn = 0   # back to player's turn
        self.move_timer = 0.0

    # ── Utility ───────────────────────────────────────────────────────

    def set_player_path(self, path: List[Tuple], nodes: int, ms: float, algo: str):
        self.player_path  = path
        self.player_step  = 0
        self.player_metrics.nodes_explored = nodes
        self.player_metrics.path_length    = len(path)
        self.player_metrics.exec_time_ms   = ms
        self.player_metrics.algorithm      = algo

    def set_enemy_metrics(self, nodes: int):
        self.enemy_metrics.nodes_explored = nodes