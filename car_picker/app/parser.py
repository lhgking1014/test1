"""Utility functions to extract metadata from car image filenames."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class CarMeta:
    """Core metadata for a single car image."""

    id: str
    path: Path
    make: str
    model: str
    year: int
    attributes: List[str]
    thumb_path: Optional[Path] = None
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[float] = None

    @property
    def display_label(self) -> str:
        """Return the make/model/year label for UI."""
        return f"{self.make} {self.model} {self.year}"

    def is_full_view(self) -> bool:
        """Heuristic to determine whether the image likely shows the full car."""

        if self.width is None or self.height is None:
            return True

        if self.width <= self.height:
            return False

        if self.width < 640 or self.height < 360:
            return False

        ratio = self.aspect_ratio or (self.width / self.height)
        return 1.2 <= ratio <= 1.9


class FilenameParseError(ValueError):
    """Raised when the filename cannot be parsed."""


def parse_filename(path: Path) -> CarMeta:
    """Extract metadata from a filename."""

    stem = path.stem
    parts = [p.strip() for p in stem.split("_") if p.strip()]
    if len(parts) < 4:
        raise FilenameParseError(f"missing required tokens: {stem}")

    make = parts[0]
    model = parts[1]

    year_part = parts[2]
    try:
        year = int(year_part)
    except ValueError as exc:
        raise FilenameParseError(f"year parse failed: {stem}") from exc

    attributes = list(parts[3:])

    return CarMeta(
        id=stem,
        path=path,
        make=make,
        model=model,
        year=year,
        attributes=attributes,
    )


def iter_car_meta(paths: Iterable[Path]) -> Iterable[CarMeta]:
    """Yield valid metadata objects from a list of paths."""

    for path in paths:
        try:
            yield parse_filename(path)
        except FilenameParseError:
            continue

