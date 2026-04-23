import time
import math
from collections import deque

def _reconstruct(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def search(start, goal, get_neighbors, is_dfs=False):
    t0 = time.perf_counter()
    container = deque([start]) if not is_dfs else [start]
    came_from, visited, nodes = {}, {start}, 0
    while container:
        current = container.pop() if is_dfs else container.popleft()
        nodes += 1
        if current == goal:
            elapsed = (time.perf_counter() - t0) * 1000
            return _reconstruct(came_from, current), nodes, elapsed
        for nb in get_neighbors(*current):
            if nb not in visited:
                visited.add(nb)
                came_from[nb] = current
                container.append(nb)
    elapsed = (time.perf_counter() - t0) * 1000
    return [], nodes, elapsed

def astar(start, goal, get_neighbors, enemy_pos=None):
    import heapq
    t0 = time.perf_counter()
    nodes = 0
    open_set = []
    heapq.heappush(open_set, (manhattan(start, goal), 0, start))
    came_from, g_score, in_open = {}, {start: 0}, {start: True}
    while open_set:
        f, g, current = heapq.heappop(open_set)
        if not in_open.get(current): continue
        in_open[current] = False
        nodes += 1
        if current == goal:
            elapsed = (time.perf_counter() - t0) * 1000
            return _reconstruct(came_from, current), nodes, elapsed
        for nb in get_neighbors(*current):
            penalty = 0
            if enemy_pos:
                dist = manhattan(nb, enemy_pos)
                if dist < 3: penalty = (3 - dist) * 10
            tentative_g = g_score[current] + 1 + penalty
            if tentative_g < g_score.get(nb, math.inf):
                came_from[nb] = current
                g_score[nb] = tentative_g
                f_new = tentative_g + manhattan(nb, goal)
                heapq.heappush(open_set, (f_new, tentative_g, nb))
                in_open[nb] = True
    elapsed = (time.perf_counter() - t0) * 1000
    return [], nodes, elapsed

class AlphaBetaEnemy:
    def __init__(self, depth=5):
        self.depth = depth
        self.nodes_explored = 0
    def best_move(self, enemy_pos, player_pos, goal_pos, get_neighbors):
        self.nodes_explored = 0
        best_val, best_next = -math.inf, None
        for nb in get_neighbors(*enemy_pos):
            if nb == player_pos: return nb
            val = self._minimax(nb, player_pos, goal_pos, self.depth - 1, False, -math.inf, math.inf, get_neighbors)
            if val > best_val:
                best_val, best_next = val, nb
        return best_next
    def _evaluate(self, enemy, player, goal):
        d_ep, d_pg = manhattan(enemy, player), manhattan(player, goal)
        if d_ep == 0: return 1000.0
        if player == goal: return -1000.0
        return -2.0 * d_ep + 1.0 * d_pg
    def _minimax(self, enemy, player, goal, depth, is_max, alpha, beta, get_neighbors):
        self.nodes_explored += 1
        if depth == 0 or enemy == player or player == goal:
            return self._evaluate(enemy, player, goal)
        if is_max:
            value = -math.inf
            for nb in get_neighbors(*enemy):
                value = max(value, self._minimax(nb, player, goal, depth - 1, False, alpha, beta, get_neighbors))
                alpha = max(alpha, value)
                if beta <= alpha: break
            return value
        else:
            value = math.inf
            for nb in get_neighbors(*player):
                value = min(value, self._minimax(enemy, nb, goal, depth - 1, True, alpha, beta, get_neighbors))
                beta = min(beta, value)
                if beta <= alpha: break
            return value

ALGORITHM_NAMES = ["BFS", "DFS", "A* (Manhattan)", "A* Smart (Avoid Enemy)"]

def run_algorithm(name, start, goal, get_neighbors, enemy_pos=None):
    if name == "BFS":
        return search(start, goal, get_neighbors, is_dfs=False)
    if name == "DFS":
        return search(start, goal, get_neighbors, is_dfs=True)
    if name == "A* (Manhattan)":
        return astar(start, goal, get_neighbors)
    if name == "A* Smart (Avoid Enemy)":
        return astar(start, goal, get_neighbors, enemy_pos)
    raise ValueError(f"Unknown algorithm: {name}")