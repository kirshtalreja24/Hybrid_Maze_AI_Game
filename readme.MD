# Hybrid Maze AI — Search Algorithm Visualiser

**Group Members:** 23K-0021 (Kirsh Kumar) · 23K-0775 (Manmohan) · 23K-0566 (Hamza Humayu)

---

## Overview

An interactive maze game that visualises and compares classical AI search algorithms in a live game environment:

| Category | Algorithms |
|---|---|
| Uninformed | BFS (Breadth-First Search), DFS (Depth-First Search) |
| Informed | A\* with Manhattan distance heuristic |
| Adversarial | Minimax + Alpha-Beta Pruning (Enemy Agent) |

- **Maze**: Randomly generated perfect maze (Recursive Backtracking), configurable size ≥ 5×5  
- **Player**: Follows BFS / DFS / A\* path automatically, or you drive it with arrow keys  
- **Enemy**: Always uses Minimax + Alpha-Beta Pruning to intercept the player

---

## Files

```
maze_game/
├── main.py          ← Entry point / game loop
├── maze.py          ← Maze generator (Recursive Backtracking)
├── algorithms.py    ← BFS, DFS, A*, Minimax + Alpha-Beta
├── game_state.py    ← Turn management, win/loss, metrics
├── renderer.py      ← Pygame drawing engine + UI panel
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Install Python 3.10+
Make sure you have Python 3.10 or newer.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the game
```bash
python main.py
```

---

## How to Play

### Controls

| Action | Input |
|---|---|
| Start / Restart | Click **▶ Start / Restart** button |
| Step one move | Click **⏭ Step** or press **Space** |
| Auto-animate | Click **⚡ Auto-Run** (toggles) |
| New random maze | Click **🔀 New Maze** |
| Restart same maze | Press **R** |
| Quit | Press **ESC** |
| Move player (Human mode) | Arrow keys or WASD |

### UI Panel (left side)

- **Player Algorithm** dropdown — choose BFS, DFS, or A\*  
  *(Alpha-Beta is the Enemy only; if selected, A\* is used for the player)*
- **Player Mode** dropdown — AI Player (auto-follows path) or Human Player (keyboard)
- **Maze Size slider** — 5×5 to 25×25; drag before clicking New Maze
- **Metrics** — shows nodes explored, path length, execution time for both agents

### Win / Lose

- **Player reaches the ◆ goal** → You (or AI) win!
- **Enemy catches the player** → Game over!

---

## Algorithm Details

### BFS
Explores all nodes at depth d before depth d+1. Guarantees shortest path. Explores more nodes than A\*.

### DFS
Follows one branch as deep as possible before backtracking. Fast but non-optimal path.

### A\* (Manhattan)
Uses `f(n) = g(n) + h(n)` where h is Manhattan distance. Optimal and efficient.

### Minimax + Alpha-Beta Pruning
- **MAX** = Enemy (minimises distance to player)
- **MIN** = Player (maximises distance from enemy)
- **Alpha-Beta** prunes branches that cannot affect the result, speeding up search significantly
- Search depth: 4 plies (configurable in `algorithms.py` → `AlphaBetaEnemy(depth=4)`)

---

## Customisation

| Setting | File | Variable |
|---|---|---|
| Enemy search depth | `algorithms.py` | `AlphaBetaEnemy(depth=N)` |
| Auto-run speed | `main.py` | `AUTO_DELAY` (seconds) |
| Min/max cell pixel size | `renderer.py` | `MIN_CELL_PX`, `MAX_CELL_PX` |
| Maze size range | `renderer.py → UIPanel` | slider `min_val`, `max_val` |
| Colour palette | `renderer.py` | `C_*` constants at top |