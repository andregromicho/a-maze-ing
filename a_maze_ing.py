#!/usr/bin/env python3
"""Generate a maze and provide the required terminal interactions."""

import sys

from mazegen import Maze


def run(config_path: str) -> int:
    """Generate and save a maze, then handle the interactive menu."""
    try:
        maze = Maze(config_path)
        maze.generate()
        maze.save_to_file()
    except KeyboardInterrupt:
        print("\nMaze generation cancelled.")
        return 130
    except (OSError, ValueError) as error:
        print(f"Error: {error}")
        return 1

    maze.drawer.draw_maze(maze.entry)
    show_path = False
    path = maze.solve_bfs()

    while True:
        print("\n=== A-Maze-ing ===")
        print("1. Generate a new maze")
        print("2. Show/Hide shortest path")
        print("3. Change wall color")
        print("4. Animate the solution")
        print("5. Quit")
        try:
            choice = input("Choice (1-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0

        if choice == "1":
            try:
                maze.generate()
                maze.save_to_file()
                path = maze.solve_bfs()
                show_path = False
                maze.drawer.draw_maze(maze.entry)
            except (OSError, ValueError) as error:
                print(f"Could not generate maze: {error}")
        elif choice == "2":
            show_path = not show_path
            if show_path and not path:
                print("No path found between entry and exit.")
                show_path = False
            else:
                if show_path:
                    print(f"Shortest path: {len(path) - 1} steps.")
                maze.drawer.draw_maze(
                    maze.entry,
                    path if show_path else None,
                )
        elif choice == "3":
            maze.drawer.rotate_color()
            maze.drawer.draw_maze(
                maze.entry,
                path if show_path else None,
            )
        elif choice == "4":
            if not path:
                print("No path found between entry and exit.")
                continue
            try:
                maze.drawer.animate_path(path)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                return 0
            show_path = True
        elif choice == "5":
            print("Goodbye!")
            return 0
        else:
            print("Invalid choice; enter a number from 1 to 5.")


def main() -> int:
    """Validate arguments and start the application."""
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py <config_file>")
        return 1
    return run(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())
