import random

class Maze:
    WALL = 1
    PATH = 0
    def __init__(self, rows, cols, seed=None):
        if rows < 5 or cols < 5:
            raise ValueError("Maze must be at least 5x5")
        self.rows = rows
        self.cols = cols
        self.seed = seed if seed is not None else random.randint(0, 99999)
        self.grid = []
        self.start = (0, 0)   
        self.goal = (rows - 1, cols - 1)
        self._generate()
    def _cell_to_pixel(self, r, c):
        return (2 * r + 1, 2 * c + 1)
    def _pixel_to_cell(self, pr, pc):
        return ((pr - 1) // 2, (pc - 1) // 2)
    def _generate(self):
        rng = random.Random(self.seed)
        H = 2 * self.rows + 1
        W = 2 * self.cols + 1
        self.grid = [[self.WALL] * W for _ in range(H)]
        visited = set()
        def carve(r, c):
            visited.add((r, c))
            pr, pc = self._cell_to_pixel(r, c)
            self.grid[pr][pc] = self.PATH
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            rng.shuffle(directions)
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols and (nr, nc) not in visited:
                    wr, wc = pr + dr, pc + dc
                    self.grid[wr][wc] = self.PATH
                    carve(nr, nc)
        carve(0, 0)
        sr, sc = self._cell_to_pixel(*self.start)
        gr, gc = self._cell_to_pixel(*self.goal)
        self.grid[sr][sc] = self.PATH
        self.grid[gr][gc] = self.PATH
    def is_wall(self, r, c):
        return self.grid[r][c] == self.WALL
    def internal_size(self):
        return len(self.grid), len(self.grid[0])
    def get_neighbors(self, r, c):
        neighbors = []
        pr, pc = self._cell_to_pixel(r, c)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            wr, wc = pr + dr, pc + dc
            nr, nc = (pr + 2 * dr), (pc + 2 * dc)
            if (0 <= wr < len(self.grid) and 0 <= wc < len(self.grid[0]) and
                    0 <= nr < len(self.grid) and 0 <= nc < len(self.grid[0])):
                if self.grid[wr][wc] == self.PATH:
                    ln, lc = self._pixel_to_cell(nr, nc)
                    neighbors.append((ln, lc))
        return neighbors
    def cell_to_internal(self, r, c):
        return self._cell_to_pixel(r, c)
    def regenerate(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 99999)
        self._generate()