*This project has been created as part of the 42 curriculum by abrandao, goperez-.*

# A-Maze-ing

## Description

A-Maze-ing is a Python maze generator. It reads a configuration file, generates
a maze, displays it in the terminal, and writes its walls and shortest path to
an output file. The terminal menu can regenerate the maze, show or hide the
shortest path, change wall colors, and animate the solution.

In an interactive terminal, each maze position uses two character columns to
compensate for the terminal's taller character cells and keep the maze
proportions balanced. Walls are filled with bright white against black
passages by default; the menu cycles through other wall colors, and the 42
pattern is highlighted in light cyan. When output is redirected, the ASCII
display uses `#` for walls and spaces for passages. Both displays mark the
entry and exit with `S` and `E`, the solution path with `*`, and the animated
position with `@`. For large mazes, use a terminal wide and tall enough to
show the whole drawing.

## Instructions

The project requires Python 3.10 or later.

Install the tools used for linting, type checking, and packaging:

```sh
make install
```

Run the project with the required subject command:

```sh
python3 a_maze_ing.py config.txt
```

Run linting and type checks with `make lint`; run the tests with `make test`.
Build the reusable `mazegen` package with `make package`.

## Configuration

The configuration file contains one `KEY=VALUE` pair per line. Empty lines,
lines starting with `#`, and text after an inline `#` are ignored.

| Key | Required | Description | Example |
| --- | --- | --- | --- |
| `WIDTH` | Yes | Maze width in cells | `WIDTH=50` |
| `HEIGHT` | Yes | Maze height in cells | `HEIGHT=19` |
| `ENTRY` | Yes | Entry cell as `x,y` | `ENTRY=0,0` |
| `EXIT` | Yes | Exit cell as `x,y` | `EXIT=49,18` |
| `OUTPUT_FILE` | Yes | File where the maze is saved | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | Yes | `True` for one path; `False` for a playable board | `PERFECT=False` |
| `SEED` | No | Integer used for reproducible generation | `SEED=42` |

`PERFECT=False` is used by the default configuration. The generator also
supports `True`, `False`, `1`, and `0` for the `PERFECT` value.

## Maze generation

The generator uses iterative depth-first search with backtracking to create a
connected spanning tree. This provides a perfect maze: there is one path between
each pair of reachable cells. In non-perfect mode, additional walls are opened
to create loops and reduce dead ends. The generator avoids opening a 3-by-3
area and reserves closed cells to draw the “42” pattern when the maze is large
enough.

## Reusable module

The `mazegen` package contains the generator, configuration parser, and terminal
renderer. The built wheel and source archive at the repository root can be
installed with `pip`. To use the package from Python:

```python
from mazegen import Maze

maze = Maze("config.txt")
maze.generate()
solution = maze.solve_bfs()
print(maze.grid)
```

`maze.grid` is a two-dimensional list of cells. Each cell has `N`, `E`, `S`,
and `W` Boolean wall values, plus a `visited` value. Coordinates in the
configuration and output use `x,y`; internal coordinates use `(row, column)`.
`solve_bfs()` returns the shortest solution as a list of `(row, column)` cells.

## Team and project management

The project authors, abrandao and goperez-, shared work on the generator,
configuration, output format, terminal display, and testing.

The work progressed from configuration parsing and maze generation to solving,
visualization, output serialization, and validation. The separated generator
and renderer make the maze logic reusable. More automated tests and additional
generation algorithms would be useful future improvements.

Tools used: Python, Make, flake8, mypy, and the standard-library `unittest`
module.

## Resources

- [Python documentation](https://docs.python.org/3/)
- [PEP 8](https://peps.python.org/pep-0008/)
- [PEP 257](https://peps.python.org/pep-0257/)
- [Depth-first search](https://en.wikipedia.org/wiki/Depth-first_search)
- [Breadth-first search](https://en.wikipedia.org/wiki/Breadth-first_search)

AI assistance was used to review subject compliance, refactor code, identify
edge cases, and help create tests. The project authors should review and
understand the implementation before evaluation.
