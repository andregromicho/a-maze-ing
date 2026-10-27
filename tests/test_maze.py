"""Tests for configuration, generation, and maze serialization."""

from collections import deque
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from mazegen import Maze
from mazegen.config import ConfigurationError, MazeConfig
from mazegen.types import Wall
from a_maze_ing import run


class MazeTests(unittest.TestCase):
    """Exercise the subject's required maze behaviors."""

    class TerminalOutput(StringIO):
        """Capture output while advertising an interactive terminal."""

        def isatty(self) -> bool:
            return True

    def _create_maze(
        self,
        directory: str,
        *,
        width: int = 15,
        height: int = 11,
        entry: str = "0,0",
        exit_cell: str | None = None,
        perfect: bool = True,
        seed: int = 42,
    ) -> Maze:
        """Create a maze from a temporary subject-format config."""
        if exit_cell is None:
            exit_cell = f"{width - 1},{height - 1}"
        output = Path(directory) / "maze.txt"
        config_file = Path(directory) / "config.txt"
        config_file.write_text(
            f"WIDTH={width}\n"
            f"HEIGHT={height}\n"
            f"ENTRY={entry}\n"
            f"EXIT={exit_cell}\n"
            f"OUTPUT_FILE={output}\n"
            f"PERFECT={perfect}\n"
            f"SEED={seed}\n",
            encoding="utf-8",
        )
        maze = Maze(config_file)
        with redirect_stdout(StringIO()):
            maze.generate()
        return maze

    def test_perfect_maze_is_connected_and_has_no_loops(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            maze = self._create_maze(directory)

        self.assertTrue(maze.solve_bfs())
        self.assertEqual(maze._loop_count(), 0)
        self.assertTrue(
            all(cell["visited"] for row in maze.grid for cell in row)
        )
        self.assertEqual(
            maze._open_edges(),
            len(maze._active_cells()) - 1,
        )
        self._assert_connected(maze)
        self._assert_wall_consistency(maze)
        self._assert_boundaries_closed(maze)

    def test_seed_reproduces_maze(self) -> None:
        with tempfile.TemporaryDirectory() as first_directory:
            first = self._create_maze(first_directory)
            first_walls = [
                [first._cell_to_hex((row, column))
                 for column in range(first.width)]
                for row in range(first.height)
            ]
        with tempfile.TemporaryDirectory() as second_directory:
            second = self._create_maze(second_directory)
            second_walls = [
                [second._cell_to_hex((row, column))
                 for column in range(second.width)]
                for row in range(second.height)
            ]
        self.assertEqual(first_walls, second_walls)

    def test_nonperfect_maze_is_playable_without_open_3x3(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            maze = self._create_maze(
                directory,
                width=50,
                height=19,
                perfect=False,
            )

        self.assertGreaterEqual(maze._loop_count(), 2)
        self.assertLessEqual(len(maze._dead_ends()), 3)
        self.assertTrue(maze.solve_bfs())
        self._assert_connected(maze)
        self._assert_wall_consistency(maze)
        for row in range(maze.height - 2):
            for column in range(maze.width - 2):
                self.assertFalse(maze._is_open_3x3(row, column))
        for cell in (
            (0, 0),
            (0, maze.width - 1),
            (maze.height - 1, 0),
            (maze.height - 1, maze.width - 1),
            (maze.height // 2, maze.width // 2),
        ):
            self.assertGreater(maze._degree(cell), 0)
        self._assert_boundaries_closed(maze)

    def test_pattern_does_not_block_entry_or_exit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            maze = self._create_maze(
                directory,
                width=9,
                height=7,
                entry="0,0",
                exit_cell="1,1",
            )

        self.assertNotIn(maze.entry, maze.pattern_42_cells)
        self.assertNotIn(maze.exit, maze.pattern_42_cells)
        self.assertTrue(maze.solve_bfs())

    def test_output_contains_hex_rows_coordinates_and_valid_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            maze = self._create_maze(directory, width=5, height=4)
            maze.save_to_file()
            lines = Path(maze.output_file).read_text(
                encoding="utf-8"
            ).splitlines()

        self.assertEqual(len(lines), maze.height + 4)
        self.assertTrue(all(len(line) == maze.width for line in lines[:4]))
        self.assertTrue(all(set(line) <= set("0123456789ABCDEF")
                            for line in lines[:4]))
        self.assertEqual(lines[4], "")
        self.assertEqual(lines[5], "0,0")
        self.assertEqual(lines[6], "4,3")
        expected_path = maze.path_to_directions(maze.solve_bfs())
        self.assertEqual(lines[7], expected_path)
        self.assertTrue(lines[7])
        self._assert_path_is_valid(maze, lines[7])

    def test_regeneration_advances_a_reproducible_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as first_directory:
            first = self._create_maze(first_directory)
            original = self._wall_rows(first)
            first.generate()
            regenerated = self._wall_rows(first)
        with tempfile.TemporaryDirectory() as second_directory:
            second = self._create_maze(second_directory)
            second.generate()
            reproduced = self._wall_rows(second)

        self.assertNotEqual(original, regenerated)
        self.assertEqual(regenerated, reproduced)

    def test_invalid_configuration_reports_actionable_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "config.txt"
            config_file.write_text(
                "WIDTH=2\nWIDTH=3\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ConfigurationError,
                "duplicate key",
            ):
                MazeConfig.from_file(config_file)

    def test_required_cli_entry_point_generates_output_and_exits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "maze.txt"
            config_file = Path(directory) / "config.txt"
            config_file.write_text(
                f"WIDTH=3\nHEIGHT=3\nENTRY=0,0\nEXIT=2,2\n"
                f"OUTPUT_FILE={output}\nPERFECT=True\nSEED=7\n",
                encoding="utf-8",
            )
            with (
                redirect_stdout(StringIO()),
                patch("builtins.input", return_value="5"),
            ):
                exit_code = run(str(config_file))
            output_exists = output.is_file()

        self.assertEqual(exit_code, 0)
        self.assertTrue(output_exists)

    def test_renderer_uses_visible_ascii_walls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            maze = self._create_maze(directory, width=5, height=4)
            output = StringIO()
            with redirect_stdout(output):
                maze.drawer.draw_maze(maze.entry)

        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), maze.height * 2 + 1)
        self.assertTrue(all(len(line) == maze.width * 2 + 1 for line in lines))
        self.assertIn("#", output.getvalue())
        self.assertIn("@", output.getvalue())
        self.assertIn("E", output.getvalue())
        self.assertNotIn("\033[", output.getvalue())
        self.assertNotIn("██", output.getvalue())

    def test_interactive_renderer_uses_contrasting_wall_and_passage_colors(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            maze = self._create_maze(directory, width=9, height=7)
            output = self.TerminalOutput()
            with redirect_stdout(output):
                maze.drawer.draw_maze(maze.entry)
                maze.drawer.rotate_color()
                maze.drawer.draw_maze(maze.entry)

        self.assertIn("\033[107;30m  \033[0m", output.getvalue())
        self.assertIn("\033[40m  \033[0m", output.getvalue())
        self.assertIn("\033[103;30m  \033[0m", output.getvalue())
        self.assertEqual(
            output.getvalue().count("\033[106;30m. \033[0m"),
            len(maze.pattern_42_cells) * 2,
        )

        frame = output.getvalue().split("\033[2J\033[H")[-1]
        visible_lines = [
            re.sub(r"\033\[[0-9;]*m", "", line)
            for line in frame.splitlines()
        ]
        self.assertTrue(
            all(
                len(line) == (maze.width * 2 + 1) * 2
                for line in visible_lines
            )
        )

    def test_animation_clears_terminal_before_each_frame(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            maze = self._create_maze(directory, width=3, height=3)
            path = maze.solve_bfs()[:3]
            output = self.TerminalOutput()
            with (
                patch("sys.stdout", output),
                patch("mazegen.draw_maze.time.sleep"),
            ):
                maze.drawer.animate_path(path)

        self.assertEqual(
            output.getvalue().count("\033[2J\033[H"),
            len(path),
        )
        self.assertIn("\033[?25l", output.getvalue())
        self.assertIn("\033[?25h", output.getvalue())

    def test_animation_has_no_terminal_controls_when_redirected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            maze = self._create_maze(directory, width=3, height=3)
            output = StringIO()
            with (
                redirect_stdout(output),
                patch("mazegen.draw_maze.time.sleep"),
            ):
                maze.drawer.animate_path(maze.solve_bfs()[:2])

        self.assertNotIn("\033[", output.getvalue())

    def _assert_boundaries_closed(self, maze: Maze) -> None:
        for row in range(maze.height):
            for column in range(maze.width):
                cell = maze.grid[row][column]
                if row == 0:
                    self.assertTrue(cell["N"])
                if row == maze.height - 1:
                    self.assertTrue(cell["S"])
                if column == 0:
                    self.assertTrue(cell["W"])
                if column == maze.width - 1:
                    self.assertTrue(cell["E"])

    def _assert_connected(self, maze: Maze) -> None:
        active = maze._active_cells()
        reached = {maze.entry}
        queue = deque([maze.entry])
        directions: tuple[tuple[int, int, Wall, Wall], ...] = (
            (-1, 0, "N", "S"),
            (0, 1, "E", "W"),
            (1, 0, "S", "N"),
            (0, -1, "W", "E"),
        )
        while queue:
            row, column = queue.popleft()
            for row_delta, column_delta, wall, _ in directions:
                neighbor = row + row_delta, column + column_delta
                if (
                    not maze.grid[row][column][wall]
                    and neighbor in active
                    and neighbor not in reached
                ):
                    reached.add(neighbor)
                    queue.append(neighbor)
        self.assertEqual(reached, active)

    def _assert_wall_consistency(self, maze: Maze) -> None:
        active = maze._active_cells()
        opposites: dict[Wall, tuple[int, int, Wall]] = {
            "N": (-1, 0, "S"),
            "E": (0, 1, "W"),
            "S": (1, 0, "N"),
            "W": (0, -1, "E"),
        }
        for row in range(maze.height):
            for column in range(maze.width):
                for wall, (row_delta, column_delta, opposite) in (
                    opposites.items()
                ):
                    neighbor = row + row_delta, column + column_delta
                    if neighbor in active:
                        self.assertEqual(
                            maze.grid[row][column][wall],
                            maze.grid[neighbor[0]][neighbor[1]][opposite],
                        )

    def _assert_path_is_valid(self, maze: Maze, path: str) -> None:
        current = maze.entry
        for direction in path:
            wall: Wall
            if direction == "N":
                row_delta, column_delta, wall = -1, 0, "N"
            elif direction == "E":
                row_delta, column_delta, wall = 0, 1, "E"
            elif direction == "S":
                row_delta, column_delta, wall = 1, 0, "S"
            elif direction == "W":
                row_delta, column_delta, wall = 0, -1, "W"
            else:
                self.fail(f"invalid path direction: {direction}")
            row, column = current
            self.assertFalse(maze.grid[row][column][wall])
            current = row + row_delta, column + column_delta
        self.assertEqual(current, maze.exit)

    @staticmethod
    def _wall_rows(maze: Maze) -> list[list[str]]:
        return [
            [maze._cell_to_hex((row, column))
             for column in range(maze.width)]
            for row in range(maze.height)
        ]


if __name__ == "__main__":
    unittest.main()
