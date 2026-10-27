import sys
import time
from typing import Protocol

from .types import Cell, Coord


class MazeLike(Protocol):
    """Minimal maze interface needed by the renderer."""

    width: int
    height: int
    entry: Coord
    exit: Coord
    grid: list[list[Cell]]
    pattern_42_cells: set[Coord]


class DrawMaze:
    """Render and animate the maze in the terminal."""

    _color_index: int
    COLORS = [
        "\033[107;30m",
        "\033[103;30m",
        "\033[102;30m",
        "\033[106;30m",
        "\033[104;30m",
        "\033[101;30m",
    ]
    PASSAGE_COLOR = "\033[40m"
    PATTERN_COLOR = "\033[106;30m"
    RESET = "\033[0m"

    def rotate_color(self) -> None:
        """Cycle to the next wall color."""
        self._color_index = (self._color_index + 1) % len(self.COLORS)

    def __init__(self, maze: MazeLike) -> None:
        """Store maze reference used by all draw operations."""
        self.maze = maze
        self._color_index = 0

    def _is_42_cell(self, y: int, x: int) -> bool:
        """Return whether a cell belongs to the reserved 42 pattern."""
        return (y, x) in self.maze.pattern_42_cells

    def _build_render_grid(self) -> list[list[str]]:
        """Build a character grid where walls are visible on dark terminals."""
        h = self.maze.height
        w = self.maze.width
        render = [["#"] * (w * 2 + 1) for _ in range(h * 2 + 1)]

        for y in range(h):
            for x in range(w):
                ry = y * 2 + 1
                rx = x * 2 + 1
                cell = self.maze.grid[y][x]

                if self._is_42_cell(y, x):
                    render[ry][rx] = "."
                    continue

                render[ry][rx] = " "
                if not cell["N"]:
                    render[ry - 1][rx] = " "
                if not cell["S"]:
                    render[ry + 1][rx] = " "
                if not cell["W"]:
                    render[ry][rx - 1] = " "
                if not cell["E"]:
                    render[ry][rx + 1] = " "

        return render

    def draw_maze(
        self,
        current_cell: Coord,
        path: list[Coord] | None = None,
    ) -> None:
        """Draw walls, passages, endpoints, pattern, and optional solution."""
        render = self._build_render_grid()
        path_cells = set(path or [])

        for row, column in path_cells:
            render[row * 2 + 1][column * 2 + 1] = "*"
        for row, column in self.maze.pattern_42_cells:
            render[row * 2 + 1][column * 2 + 1] = "."
        entry_row, entry_column = self.maze.entry
        exit_row, exit_column = self.maze.exit
        render[entry_row * 2 + 1][entry_column * 2 + 1] = "S"
        render[exit_row * 2 + 1][exit_column * 2 + 1] = "E"
        current_row, current_column = current_cell
        render[current_row * 2 + 1][current_column * 2 + 1] = "@"

        interactive = sys.stdout.isatty()
        if interactive:
            sys.stdout.write("\033[2J\033[H")

        wall_color = self.COLORS[self._color_index]
        cell_colors = {
            ".": "\033[90m",
            "*": "\033[91m",
            "@": "\033[95m",
            "S": "\033[95m",
            "E": "\033[91m",
        }
        for line in render:
            if interactive:
                output = "".join(
                    f"{wall_color}  {self.RESET}"
                    if char == "#"
                    else f"{self.PASSAGE_COLOR}  {self.RESET}"
                    if char == " "
                    else f"{self.PATTERN_COLOR}{char} {self.RESET}"
                    if char == "."
                    else f"{cell_colors[char]}{char} {self.RESET}"
                    if char in cell_colors
                    else f"{char} "
                    for char in line
                )
            else:
                output = "".join(line)
            sys.stdout.write(output + "\n")

        sys.stdout.flush()

    def animate_path(
        self,
        path: list[Coord],
        delay: float = 0.1,
    ) -> None:
        """Animate a path by progressively revealing its cells."""
        interactive = sys.stdout.isatty()
        if interactive:
            sys.stdout.write("\033[?25l")
        try:
            for i in range(1, len(path) + 1):
                self.draw_maze(path[i - 1], path[:i])
                time.sleep(delay)
        finally:
            if interactive:
                sys.stdout.write("\033[?25h")
                sys.stdout.flush()
