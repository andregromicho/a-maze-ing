"""Configuration loading and validation for maze generation."""

from dataclasses import dataclass
from pathlib import Path

from .types import Coord


class ConfigurationError(ValueError):
    """Raised when the maze configuration is invalid or cannot be read."""


@dataclass(frozen=True)
class MazeConfig:
    """Validated options used to generate and save a maze."""

    width: int
    height: int
    entry: Coord
    exit: Coord
    output_file: str
    perfect: bool
    seed: int | None = None

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ConfigurationError("WIDTH and HEIGHT must be greater than 0")
        if self.entry == self.exit:
            raise ConfigurationError("ENTRY and EXIT must be different cells")
        for name, (row, column) in (
            ("ENTRY", self.entry),
            ("EXIT", self.exit),
        ):
            if not (0 <= row < self.height and 0 <= column < self.width):
                raise ConfigurationError(
                    f"{name} coordinates are outside the maze"
                )
        if not self.output_file.strip():
            raise ConfigurationError("OUTPUT_FILE must not be empty")

    @classmethod
    def from_file(cls, filename: str | Path) -> "MazeConfig":
        """Parse and validate a KEY=VALUE configuration file."""
        path = Path(filename)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            raise ConfigurationError(
                f"cannot read configuration '{path}': {error}"
            ) from error

        values: dict[str, str] = {}
        allowed_keys = {
            "WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT",
            "SEED",
        }
        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            if "=" not in line:
                raise ConfigurationError(
                    f"line {line_number}: expected KEY=VALUE"
                )

            key, value = (part.strip() for part in line.split("=", 1))
            key = key.upper()
            if key not in allowed_keys:
                raise ConfigurationError(
                    f"line {line_number}: unknown key '{key}'"
                )
            if not value:
                raise ConfigurationError(
                    f"line {line_number}: missing value for {key}"
                )
            if key in values:
                raise ConfigurationError(
                    f"line {line_number}: duplicate key '{key}'"
                )
            values[key] = value

        required = {
            "WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT",
        }
        missing = sorted(required - values.keys())
        if missing:
            raise ConfigurationError(
                f"missing required keys: {', '.join(missing)}"
            )

        try:
            width = int(values["WIDTH"])
            height = int(values["HEIGHT"])
            entry = cls._parse_coordinate(values["ENTRY"])
            exit_cell = cls._parse_coordinate(values["EXIT"])
            perfect = cls._parse_boolean(values["PERFECT"])
            seed = int(values["SEED"]) if "SEED" in values else None
        except ValueError as error:
            raise ConfigurationError(str(error)) from error

        return cls(
            width=width,
            height=height,
            entry=entry,
            exit=exit_cell,
            output_file=values["OUTPUT_FILE"],
            perfect=perfect,
            seed=seed,
        )

    @staticmethod
    def _parse_coordinate(value: str) -> Coord:
        """Parse external x,y coordinates as internal row,column values."""
        parts = value.split(",")
        if len(parts) != 2:
            raise ConfigurationError(
                "coordinates must use the x,y format"
            )
        try:
            column, row = (int(part.strip()) for part in parts)
        except ValueError as error:
            raise ConfigurationError(
                f"invalid coordinate '{value}'"
            ) from error
        return row, column

    @staticmethod
    def _parse_boolean(value: str) -> bool:
        """Parse the boolean values commonly used in configuration files."""
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
        raise ConfigurationError(
            "PERFECT must be True or False"
        )
