from typing import Literal, TypeAlias, TypedDict

Coord: TypeAlias = tuple[int, int]
Wall: TypeAlias = Literal["N", "E", "S", "W"]


class Cell(TypedDict):
    """Wall and traversal state for one maze cell."""

    visited: bool
    N: bool
    E: bool
    S: bool
    W: bool
