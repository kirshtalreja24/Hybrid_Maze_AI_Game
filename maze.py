import random
from typing import List, Tuple, Set


class Maze:
    WALL = 1
    PATH = 0

    def __init__(self, rows: int, cols: int, seed: int = None):
        if rows < 5 or cols < 5:
            raise ValueError("Maze must be at least 5x5")
        # Internally we use (2*rows+1) x (2*cols+1) so walls are cells too
        self.rows = rows
        self.cols = cols
        self.seed = seed if seed is not None else random.randint(0, 99999)
        self.grid: List[List[int]] = []
        self.start: Tuple[int, int] = (0, 0)   
        self.goal: Tuple[int, int] = (rows - 1, cols - 1)
        self._generate()


    def _cell_to_pixel(self, r: int, c: int) -> Tuple[int, int]:
        """Convert logical cell (r,c) → internal grid coords."""
        return (2 * r + 1, 2 * c + 1)

    def _pixel_to_cell(self, pr: int, pc: int) -> Tuple[int, int]:
        return ((pr - 1) // 2, (pc - 1) // 2)

    def _generate(self):
        rng = random.Random(self.seed)
        H = 2 * self.rows + 1
        W = 2 * self.cols + 1
        # Start all walls
        self.grid = [[self.WALL] * W for _ in range(H)]

        visited: Set[Tuple[int, int]] = set()

        def carve(r: int, c: int):
            visited.add((r, c))
            pr, pc = self._cell_to_pixel(r, c)
            self.grid[pr][pc] = self.PATH
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            rng.shuffle(directions)
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols and (nr, nc) not in visited:
                    # Remove wall between current and neighbor
                    wr, wc = pr + dr, pc + dc
                    self.grid[wr][wc] = self.PATH
                    carve(nr, nc)

        carve(0, 0)

        # Open start and goal borders for clarity
        sr, sc = self._cell_to_pixel(*self.start)
        gr, gc = self._cell_to_pixel(*self.goal)
        self.grid[sr][sc] = self.PATH
        self.grid[gr][gc] = self.PATH

    def is_wall(self, r: int, c: int) -> bool:
        """Check internal grid coords."""
        return self.grid[r][c] == self.WALL

    def internal_size(self) -> Tuple[int, int]:
        """Return (rows, cols) of the internal grid."""
        return len(self.grid), len(self.grid[0])

    def get_neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """
        Return walkable logical-cell neighbors of logical cell (r,c).
        """
        neighbors = []
        pr, pc = self._cell_to_pixel(r, c)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            wr, wc = pr + dr, pc + dc          # wall/path cell
            nr, nc = (pr + 2 * dr), (pc + 2 * dc)  # next logical cell (internal coords)
            # Ensure within bounds and not a wall between them
            if (0 <= wr < len(self.grid) and 0 <= wc < len(self.grid[0]) and
                    0 <= nr < len(self.grid) and 0 <= nc < len(self.grid[0])):
                if self.grid[wr][wc] == self.PATH:
                    # Convert back to logical
                    ln, lc = self._pixel_to_cell(nr, nc)
                    neighbors.append((ln, lc))
        return neighbors

    def cell_to_internal(self, r: int, c: int) -> Tuple[int, int]:
        return self._cell_to_pixel(r, c)

    def regenerate(self, seed: int = None):
        self.seed = seed if seed is not None else random.randint(0, 99999)
        self._generate()