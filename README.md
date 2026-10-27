*This project has been created as part of the 42 curriculum by abrandao, goperez-.*

# A-Maze-ing

## Description

A-Maze-ing is a Python maze generator for the 42 curriculum. It reads a
configuration file, generates a connected maze, finds a shortest route between
the entry and exit, writes the maze to a file, and displays it in the terminal.
The project also provides an interactive menu to generate another maze, show or
hide the solution, change wall colors, and animate the solution.

The generator supports perfect mazes and a non-perfect, game-style board. When
the maze is large enough, it reserves closed cells to draw a visible “42”
pattern. In an interactive terminal, walls and passages use contrasting
background colors, the pattern is highlighted, and each maze position uses two
character columns to improve its proportions. When output is redirected, the
display uses ASCII characters instead.

## Instructions

Python 3.10 or later is required. From the repository root, run the program
with one configuration-file argument:

```sh
python3 a_maze_ing.py config.txt
```

The default configuration file is `config.txt`. To use another configuration,
pass its path instead:

```sh
python3 a_maze_ing.py path/to/config.txt
```

The program generates and displays the maze, writes the result to the configured
output file, and then presents a menu:

| Choice | Action |
| --- | --- |
| `1` | Generate and display a new maze |
| `2` | Show or hide the shortest path |
| `3` | Change the wall color |
| `4` | Animate the solution |
| `5` | Quit |

Install the project's development and packaging tools with `make install`.
The Makefile also provides these commands:

| Command | Purpose |
| --- | --- |
| `make run` | Run the program using `config.txt` |
| `make test` | Run the automated tests |
| `make lint` | Run flake8 and mypy |
| `make package` | Build the reusable Python package |
| `make clean` | Remove generated caches and build artifacts |

## Configuration

The configuration is a plain-text file with one `KEY=VALUE` pair per line.
Keys are case-insensitive. Blank lines, lines starting with `#`, and text
following `#` on a line are ignored. The following keys are supported:

| Key | Required | Description | Example |
| --- | --- | --- | --- |
| `WIDTH` | Yes | Maze width in cells; must be positive | `WIDTH=20` |
| `HEIGHT` | Yes | Maze height in cells; must be positive | `HEIGHT=15` |
| `ENTRY` | Yes | Entry coordinates in `x,y` order | `ENTRY=0,0` |
| `EXIT` | Yes | Exit coordinates in `x,y` order; must differ from the entry | `EXIT=19,14` |
| `OUTPUT_FILE` | Yes | Path where the generated maze is saved | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | Yes | Selects perfect or game-style maze generation | `PERFECT=False` |
| `SEED` | No | Integer seed for reproducible generation | `SEED=42` |

`PERFECT` accepts `True` or `False` (also `1`/`0`, `yes`/`no`, `y`/`n`, and
`on`/`off`, in either case). If `SEED` is omitted, generation is not tied to a
user-specified seed.

The repository's default `config.txt` is:

```text
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE = maze.txt
PERFECT=False
```

External coordinates use `x,y`, where `x` is the column and `y` is the row.
The entry and exit must be distinct cells inside the configured maze. Invalid
configuration values and file errors are reported with an explanatory message.

## Maze generation and solving

The generator uses randomized, iterative depth-first search with
backtracking. It starts at the entry and opens a wall to an unvisited
neighbor until all non-pattern cells have been reached. This is a spanning
tree: in perfect mode (`PERFECT=True`), there is exactly one route between any
two reachable cells.

In game-style mode (`PERFECT=False`), the generator opens additional walls to
create loops and reduce dead ends. It avoids openings that would create a
fully open 3-by-3 area. When dimensions allow, the 42 pattern is placed in
closed cells without blocking the entry, exit, or required open areas. A
seeded configuration makes maze generation reproducible.

The shortest route is found with breadth-first search. The displayed solution
marks its cells with `*`; the entry and exit are marked `S` and `E`, and `@`
marks the current position during animation. The 42 pattern is shown in light
cyan in an interactive terminal.

## Output file format

The output file contains:

1. One hexadecimal character per maze cell, with one row per line. The four
   low-order bits represent walls in `N`, `E`, `S`, `W` order.
2. A blank line.
3. The entry coordinates in `x,y` order.
4. The exit coordinates in `x,y` order.
5. The shortest route as a sequence of `N`, `E`, `S`, and `W` steps.

For example, the default configuration writes 15 maze rows, followed by the
entry, exit, and route data.

## Reusable code

The `mazegen` package separates configuration parsing, maze generation and
solving, and terminal rendering from the command-line entry point. Its
`Maze` class can be used by other Python code:

```python
from mazegen import Maze

maze = Maze("config.txt")
maze.generate()
path = maze.solve_bfs()
maze.save_to_file()
```

`solve_bfs()` returns the shortest path as a list of `(row, column)` tuples.
`maze.grid` stores each cell's north, east, south, and west wall states.
Coordinates in configuration and output files use `x,y`; internal coordinates
use `(row, column)`.

Build a wheel and source distribution with `make package`. The package
metadata, including the Python version requirement and dependencies, is in
`pyproject.toml`.

## Team and project workflow

The project authors are abrandao and goperez-. The work is credited jointly:
configuration handling, generation, solving, output serialization, terminal
visualization, and testing are parts of the same project.

The implementation is organized as a progression from validated configuration
to maze generation, pathfinding and file output, and finally terminal
interaction and tests. Keeping the generator and renderer in the `mazegen`
package makes their responsibilities easier to reuse and validate separately.
The seeded generation and automated checks help verify reproducibility and
maze connectivity. Further useful improvements would include broader tests
across maze dimensions and additional generation algorithms.

Tools used include Python, Make, flake8, mypy, the standard-library `unittest`
module, and the Python `build` package.

## Resources

- [Python documentation](https://docs.python.org/3/)
- [Python `random` documentation](https://docs.python.org/3/library/random.html)
- [Python `collections.deque` documentation](https://docs.python.org/3/library/collections.html#collections.deque)
- [Python `unittest` documentation](https://docs.python.org/3/library/unittest.html)
- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Depth-first search](https://en.wikipedia.org/wiki/Depth-first_search)
- [Breadth-first search](https://en.wikipedia.org/wiki/Breadth-first_search)

AI assistance was used to review the project against the subject, improve the
terminal renderer, identify edge cases, strengthen tests, and edit this
documentation. The project authors are responsible for reviewing and
understanding the code and any AI-assisted changes.
