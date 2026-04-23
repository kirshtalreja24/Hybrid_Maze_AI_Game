"""
algorithms.py — All AI search algorithms for the Hybrid Maze Game.

Algorithms:
  - BFS  (Breadth-First Search)     — uninformed
  - DFS  (Depth-First Search)       — uninformed
  - A*   (A-Star, Manhattan dist.)  — informed
  - Minimax with Alpha-Beta Pruning — adversarial (enemy AI)

Each pathfinding function returns:
    path        : List[Tuple[int,int]]  — logical cell coords from start to goal
    nodes_explored : int
    elapsed_ms  : float
"""

import time
import math
from collections import deque
from typing import List, Tuple, Optional, Dict, Callable


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _reconstruct(came_from: Dict, current: Tuple) -> List[Tuple]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ──────────────────────────────────────────────────────────────────────
# BFS
# ──────────────────────────────────────────────────────────────────────

def bfs(start: Tuple, goal: Tuple,
        get_neighbors: Callable) -> Tuple[List[Tuple], int, float]:
    t0 = time.perf_counter()
    queue = deque([start])
    came_from: Dict = {}
    visited = {start}
    nodes = 0

    while queue:
        current = queue.popleft()
        nodes += 1
        if current == goal:
            elapsed = (time.perf_counter() - t0) * 1000
            return _reconstruct(came_from, current), nodes, elapsed
        for nb in get_neighbors(*current):
            if nb not in visited:
                visited.add(nb)
                came_from[nb] = current
                queue.append(nb)

    elapsed = (time.perf_counter() - t0) * 1000
    return [], nodes, elapsed


# ──────────────────────────────────────────────────────────────────────
# DFS
# ──────────────────────────────────────────────────────────────────────

def dfs(start: Tuple, goal: Tuple,
        get_neighbors: Callable) -> Tuple[List[Tuple], int, float]:
    t0 = time.perf_counter()
    stack = [start]
    came_from: Dict = {}
    visited = {start}
    nodes = 0

    while stack:
        current = stack.pop()
        nodes += 1
        if current == goal:
            elapsed = (time.perf_counter() - t0) * 1000
            return _reconstruct(came_from, current), nodes, elapsed
        for nb in get_neighbors(*current):
            if nb not in visited:
                visited.add(nb)
                came_from[nb] = current
                stack.append(nb)

    elapsed = (time.perf_counter() - t0) * 1000
    return [], nodes, elapsed


# ──────────────────────────────────────────────────────────────────────
# A*
# ──────────────────────────────────────────────────────────────────────

def astar(start: Tuple, goal: Tuple,
          get_neighbors: Callable) -> Tuple[List[Tuple], int, float]:
    import heapq
    t0 = time.perf_counter()
    nodes = 0

    open_set = []
    heapq.heappush(open_set, (manhattan(start, goal), 0, start))
    came_from: Dict = {}
    g_score: Dict = {start: 0}
    in_open: Dict = {start: True}

    while open_set:
        f, g, current = heapq.heappop(open_set)
        if not in_open.get(current):
            continue
        in_open[current] = False
        nodes += 1

        if current == goal:
            elapsed = (time.perf_counter() - t0) * 1000
            return _reconstruct(came_from, current), nodes, elapsed

        for nb in get_neighbors(*current):
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(nb, math.inf):
                came_from[nb] = current
                g_score[nb] = tentative_g
                f_new = tentative_g + manhattan(nb, goal)
                heapq.heappush(open_set, (f_new, tentative_g, nb))
                in_open[nb] = True

    elapsed = (time.perf_counter() - t0) * 1000
    return [], nodes, elapsed


# ──────────────────────────────────────────────────────────────────────
# Minimax with Alpha-Beta Pruning  (Enemy AI)
# ──────────────────────────────────────────────────────────────────────

class AlphaBetaEnemy:
    """
    Enemy agent that uses Minimax + Alpha-Beta pruning.

    MAX player = enemy (wants to minimize distance to player)
    MIN player = player (wants to maximize distance from enemy)

    State = (enemy_pos, player_pos)
    Evaluation = weighted combination of:
      - distance(enemy, player)
      - distance(player, goal)
    Enemy (MAX) wants to minimize distance to player and maximize player's distance to goal.
    
    depth is kept shallow (4-5) for real-time performance.
    """

    def __init__(self, depth: int = 5):
        self.depth = depth
        self.nodes_explored = 0

    def best_move(self,
                  enemy_pos: Tuple[int, int],
                  player_pos: Tuple[int, int],
                  goal_pos: Tuple[int, int],
                  get_neighbors: Callable) -> Optional[Tuple[int, int]]:
        self.nodes_explored = 0
        best_val = -math.inf
        best_next = None

        neighbors = get_neighbors(*enemy_pos)
        if not neighbors:
            return None

        for nb in neighbors:
            # If we can catch the player immediately, do it
            if nb == player_pos:
                return nb

            val = self._minimax(nb, player_pos, goal_pos, self.depth - 1,
                                False, -math.inf, math.inf, get_neighbors)
            if val > best_val:
                best_val = val
                best_next = nb

        return best_next

    def _evaluate(self, enemy: Tuple, player: Tuple, goal: Tuple) -> float:
        d_ep = manhattan(enemy, player)
        d_pg = manhattan(player, goal)
        
        # If enemy catches player, very high value for enemy
        if d_ep == 0:
            return 1000.0
        
        # If player reaches goal, very low value for enemy
        if player == goal:
            return -1000.0

        # Enemy wants d_ep to be small and d_pg to be large
        # Score = - (dist to player) + 0.5 * (player's dist to goal)
        return -2.0 * d_ep + 1.0 * d_pg

    def _minimax(self, enemy: Tuple, player: Tuple, goal: Tuple,
                 depth: int, is_max: bool,
                 alpha: float, beta: float,
                 get_neighbors: Callable) -> float:
        self.nodes_explored += 1

        # Terminal / cutoff
        if depth == 0 or enemy == player or player == goal:
            return self._evaluate(enemy, player, goal)

        if is_max:
            # Enemy's turn
            value = -math.inf
            for nb in get_neighbors(*enemy):
                value = max(value,
                            self._minimax(nb, player, goal, depth - 1,
                                          False, alpha, beta, get_neighbors))
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        else:
            # Player's turn (assumed to move towards goal while avoiding enemy)
            value = math.inf
            for nb in get_neighbors(*player):
                # We assume player is smart and tries to minimize the enemy's evaluation
                value = min(value,
                            self._minimax(enemy, nb, goal, depth - 1,
                                          True, alpha, beta, get_neighbors))
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value


# ──────────────────────────────────────────────────────────────────────
# Smart A* (Avoids Enemy)
# ──────────────────────────────────────────────────────────────────────

def astar_smart(start: Tuple, goal: Tuple, enemy_pos: Tuple,
                get_neighbors: Callable) -> Tuple[List[Tuple], int, float]:
    """A* search that adds a penalty for being close to the enemy."""
    import heapq
    t0 = time.perf_counter()
    nodes = 0

    open_set = []
    # (f_score, g_score, current_pos)
    heapq.heappush(open_set, (manhattan(start, goal), 0, start))
    came_from: Dict = {}
    g_score: Dict = {start: 0}
    in_open: Dict = {start: True}

    while open_set:
        f, g, current = heapq.heappop(open_set)
        if not in_open.get(current):
            continue
        in_open[current] = False
        nodes += 1

        if current == goal:
            elapsed = (time.perf_counter() - t0) * 1000
            return _reconstruct(came_from, current), nodes, elapsed

        for nb in get_neighbors(*current):
            # Base cost is 1, but add penalty for proximity to enemy
            dist_to_enemy = manhattan(nb, enemy_pos)
            penalty = 0
            if dist_to_enemy < 3:
                penalty = (3 - dist_to_enemy) * 10 # Strong penalty for getting close
            
            tentative_g = g_score[current] + 1 + penalty
            if tentative_g < g_score.get(nb, math.inf):
                came_from[nb] = current
                g_score[nb] = tentative_g
                f_new = tentative_g + manhattan(nb, goal)
                heapq.heappush(open_set, (f_new, tentative_g, nb))
                in_open[nb] = True

    elapsed = (time.perf_counter() - t0) * 1000
    return [], nodes, elapsed


# ──────────────────────────────────────────────────────────────────────
# Dispatcher
# ──────────────────────────────────────────────────────────────────────

ALGORITHM_NAMES = ["BFS", "DFS", "A* (Manhattan)", "A* Smart (Avoid Enemy)"]

def run_algorithm(name: str, start: Tuple, goal: Tuple,
                  get_neighbors: Callable,
                  enemy_pos: Optional[Tuple] = None) -> Tuple[List[Tuple], int, float]:
    """Run a named algorithm and return (path, nodes_explored, ms)."""
    if name == "A* Smart (Avoid Enemy)":
        return astar_smart(start, goal, enemy_pos or (999, 999), get_neighbors)

    dispatch = {
        "BFS":              bfs,
        "DFS":              dfs,
        "A* (Manhattan)":  astar,
    }
    fn = dispatch.get(name)
    if fn is None:
        raise ValueError(f"Unknown algorithm: {name}")
    return fn(start, goal, get_neighbors)