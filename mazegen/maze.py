"""Maze generation, solving, and output serialization."""

from collections import deque
from itertools import product
from pathlib import Path
from random import Random

from .config import MazeConfig
from .draw_maze import DrawMaze
from .types import Cell, Coord, Wall

PATTERN_42 = (
    (0, 0),
    (1, 0),
    (2, 0), (2, 1), (2, 2),
    (3, 2),
    (4, 2),
    (0, 4), (0, 5), (0, 6),
    (1, 6),
    (2, 4), (2, 5), (2, 6),
    (3, 4),
    (4, 4), (4, 5), (4, 6),
)

DIRECTIONS: tuple[tuple[int, int, Wall, Wall], ...] = (
    (-1, 0, "N", "S"),
    (0, 1, "E", "W"),
    (1, 0, "S", "N"),
    (0, -1, "W", "E"),
)


class Maze:
    """Generate a maze from a config file or validated configuration."""

    def __init__(self, config: str | Path | MazeConfig) -> None:
        self.config = (
            config if isinstance(config, MazeConfig)
            else MazeConfig.from_file(config)
        )
        self.width = self.config.width
        self.height = self.config.height
        self.entry = self.config.entry
        self.exit = self.config.exit
        self.output_file = self.config.output_file
        self.perfect = self.config.perfect
        self.seed = self.config.seed
        self.grid: list[list[Cell]] = []
        self.pattern_42_cells: set[Coord] = set()
        self.drawer = DrawMaze(self)
        self._rng = Random(self.seed)

    def generate(self) -> None:
        """Create a fresh maze, advancing the seeded random sequence."""
        self.build_grid()
        self.build_maze()

    def build_grid(self) -> None:
        """Reset the grid to cells surrounded by closed walls."""
        self.grid = [
            [
                {"visited": False, "N": True, "E": True, "S": True, "W": True}
                for _ in range(self.width)
            ]
            for _ in range(self.height)
        ]
        self.pattern_42_cells.clear()

    def build_maze(self) -> None:
        """Build a connected perfect maze or a playable maze with loops."""
        if not self.grid:
            raise ValueError("build_grid() must be called before build_maze()")

        self._place_42_pattern()
        self._build_spanning_tree()
        active_cells = self._active_cells()
        if not all(self.grid[row][column]["visited"]
                   for row, column in active_cells):
            raise ValueError("the maze layout is disconnected")

        if not self.perfect:
            self._braid_dead_ends()

    def _active_cells(self) -> set[Coord]:
        """Return cells that are not reserved for the visible 42 pattern."""
        return {
            (row, column)
            for row in range(self.height)
            for column in range(self.width)
            if (row, column) not in self.pattern_42_cells
        }

    def _place_42_pattern(self) -> None:
        """Place a centered 42 without blocking required open cells."""
        if self.width < 9 or self.height < 7:
            print("WARNING: maze is too small for the 42 pattern")
            return

        protected = {
            self.entry,
            self.exit,
            (self.height // 2, self.width // 2),
        }
        if not self.perfect:
            protected.update({
                (0, 0),
                (0, self.width - 1),
                (self.height - 1, 0),
                (self.height - 1, self.width - 1),
            })

        ideal_row = (self.height - 5) // 2
        ideal_column = (self.width - 7) // 2
        origins = sorted(
            product(range(self.height - 4), range(self.width - 6)),
            key=lambda origin: (
                abs(origin[0] - ideal_row) + abs(origin[1] - ideal_column),
                origin,
            ),
        )
        for start_row, start_column in origins:
            cells = {
                (start_row + row, start_column + column)
                for row, column in PATTERN_42
            }
            if cells.isdisjoint(protected):
                self.pattern_42_cells = cells
                for row, column in cells:
                    self.grid[row][column]["visited"] = True
                return

        print("WARNING: no position is available for the 42 pattern")

    def _build_spanning_tree(self) -> None:
        """Carve a connected tree with iterative depth-first search."""
        stack = [self.entry]
        self.grid[self.entry[0]][self.entry[1]]["visited"] = True

        while stack:
            current = stack[-1]
            neighbors = [
                neighbor for neighbor in self._neighbors(current)
                if not self.grid[neighbor[0]][neighbor[1]]["visited"]
            ]
            if not neighbors:
                stack.pop()
                continue

            neighbor = self._rng.choice(neighbors)
            self._remove_wall(current, neighbor)
            self.grid[neighbor[0]][neighbor[1]]["visited"] = True
            stack.append(neighbor)

    def _neighbors(self, cell: Coord) -> list[Coord]:
        """Return in-bounds neighboring cells."""
        row, column = cell
        neighbors = []
        for row_delta, column_delta, _, _ in DIRECTIONS:
            next_cell = row + row_delta, column + column_delta
            if (0 <= next_cell[0] < self.height
                    and 0 <= next_cell[1] < self.width):
                neighbors.append(next_cell)
        return neighbors

    @staticmethod
    def _wall_names(first: Coord, second: Coord) -> tuple[Wall, Wall]:
        """Return matching wall names for two adjacent cells."""
        row_delta = second[0] - first[0]
        column_delta = second[1] - first[1]
        for expected_row, expected_column, wall, opposite in DIRECTIONS:
            if (row_delta, column_delta) == (expected_row, expected_column):
                return wall, opposite
        raise ValueError("cells must be adjacent")

    def _remove_wall(self, first: Coord, second: Coord) -> None:
        """Open the shared wall between adjacent cells."""
        first_wall, second_wall = self._wall_names(first, second)
        self.grid[first[0]][first[1]][first_wall] = False
        self.grid[second[0]][second[1]][second_wall] = False

    def _degree(self, cell: Coord) -> int:
        """Count open passages connecting a cell to its neighbors."""
        row, column = cell
        return sum(not self.grid[row][column][wall]
                   for _, _, wall, _ in DIRECTIONS)

    def _open_edges(self) -> int:
        """Count open passages between active cells."""
        count = 0
        for row, column in self._active_cells():
            if column + 1 < self.width:
                count += not self.grid[row][column]["E"]
            if row + 1 < self.height:
                count += not self.grid[row][column]["S"]
        return count

    def _loop_count(self) -> int:
        """Return the number of independent cycles in the connected maze."""
        return self._open_edges() - len(self._active_cells()) + 1

    def _dead_ends(self) -> list[Coord]:
        """Return active cells connected to exactly one passage."""
        return [
            cell for cell in self._active_cells()
            if self._degree(cell) == 1
        ]

    def _is_open_3x3(self, top: int, left: int) -> bool:
        """Check whether every internal wall in a 3-by-3 area is open."""
        for row in range(top, top + 3):
            for column in range(left, left + 3):
                if column < left + 2 and self.grid[row][column]["E"]:
                    return False
                if row < top + 2 and self.grid[row][column]["S"]:
                    return False
        return True

    def _opening_creates_open_3x3(self, first: Coord, second: Coord) -> bool:
        """Check a proposed opening without leaving the grid modified."""
        first_wall, second_wall = self._wall_names(first, second)
        self.grid[first[0]][first[1]][first_wall] = False
        self.grid[second[0]][second[1]][second_wall] = False
        try:
            min_row, max_row = sorted((first[0], second[0]))
            min_column, max_column = sorted((first[1], second[1]))
            top_rows = range(
                max(0, max_row - 2),
                min(min_row, self.height - 3) + 1,
            )
            left_columns = range(
                max(0, max_column - 2),
                min(min_column, self.width - 3) + 1,
            )
            return any(
                self._is_open_3x3(top, left)
                for top in top_rows
                for left in left_columns
            )
        finally:
            self.grid[first[0]][first[1]][first_wall] = True
            self.grid[second[0]][second[1]][second_wall] = True

    def _closed_edges(self) -> list[tuple[Coord, Coord]]:
        """List closed internal walls between active neighboring cells."""
        active_cells = self._active_cells()
        edges = []
        for row, column in active_cells:
            cell = (row, column)
            for neighbor in ((row, column + 1), (row + 1, column)):
                if not (
                    0 <= neighbor[0] < self.height
                    and 0 <= neighbor[1] < self.width
                ):
                    continue
                if neighbor not in active_cells:
                    continue
                wall, _ = self._wall_names(cell, neighbor)
                if self.grid[row][column][wall]:
                    edges.append((cell, neighbor))
        return edges

    def _braid_dead_ends(self) -> None:
        """Add safe loops, limiting dead ends and 3-by-3 open areas."""
        while self._loop_count() < 2 or len(self._dead_ends()) > 2:
            candidates = [
                edge for edge in self._closed_edges()
                if not self._opening_creates_open_3x3(*edge)
            ]
            if not candidates:
                if self._loop_count() >= 2 and len(self._dead_ends()) <= 3:
                    return
                raise ValueError(
                    "maze dimensions cannot provide two loops with few "
                    "dead ends without creating an open 3x3 area"
                )

            dead_ends = set(self._dead_ends())
            best_score = max(
                sum(cell in dead_ends for cell in edge)
                for edge in candidates
            )
            best_candidates = [
                edge for edge in candidates
                if sum(cell in dead_ends for cell in edge) == best_score
            ]
            self._remove_wall(*self._rng.choice(best_candidates))

    def solve_bfs(self) -> list[Coord]:
        """Return a shortest path from entry to exit, or an empty list."""
        queue: deque[Coord] = deque([self.entry])
        previous: dict[Coord, Coord | None] = {self.entry: None}

        while queue:
            row, column = current = queue.popleft()
            if current == self.exit:
                path = []
                cursor: Coord | None = current
                while cursor is not None:
                    path.append(cursor)
                    cursor = previous[cursor]
                return list(reversed(path))

            for row_delta, column_delta, wall, _ in DIRECTIONS:
                if self.grid[row][column][wall]:
                    continue
                neighbor = row + row_delta, column + column_delta
                if neighbor not in previous:
                    previous[neighbor] = (row, column)
                    queue.append(neighbor)
        return []

    def path_to_directions(self, path: list[Coord]) -> str:
        """Convert adjacent path cells to N, E, S, and W steps."""
        directions = []
        for first, second in zip(path, path[1:]):
            wall, _ = self._wall_names(first, second)
            directions.append(wall)
        return "".join(directions)

    def save_to_file(self) -> None:
        """Write hexadecimal walls, coordinates, and a shortest path."""
        path = self.solve_bfs()
        if not path:
            raise ValueError(
                "cannot save a maze with no path from ENTRY to EXIT"
            )

        lines = [
            "".join(
                self._cell_to_hex((row, column))
                for column in range(self.width)
            )
            for row in range(self.height)
        ]
        lines.extend((
            "",
            f"{self.entry[1]},{self.entry[0]}",
            f"{self.exit[1]},{self.exit[0]}",
            self.path_to_directions(path),
        ))
        Path(self.output_file).write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

    def _cell_to_hex(self, cell: Coord) -> str:
        """Encode North, East, South, and West walls as a hexadecimal digit."""
        row, column = cell
        value = sum(
            1 << bit
            for bit, (_, _, wall, _) in enumerate(DIRECTIONS)
            if self.grid[row][column][wall]
        )
        return format(value, "X")
