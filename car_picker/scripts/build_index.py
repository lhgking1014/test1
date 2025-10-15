"""Generate index.json by scanning the car image dataset."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

if __package__ is None or __package__ == "":
    sys.path.append(str(ROOT))
    from app.parser import CarMeta, iter_car_meta  # type: ignore  # noqa: E402
else:  # pragma: no cover
    from ..app.parser import CarMeta, iter_car_meta

DATA_DIR = ROOT / "data"
OUTPUT_PATH = ROOT / "index.json"
THUMB_DIR = ROOT / "thumbs"


def scan_images(directory: Path) -> Iterable[Path]:
    """Yield image files underneath the given directory."""

    extensions = {".jpg", ".jpeg", ".png", ".webp"}
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            yield path


def build_catalog(cars: List[CarMeta]) -> dict:
    """Build helper catalogues for quick lookups."""

    makes = sorted({car.make for car in cars})
    models: Dict[str, set[str]] = defaultdict(set)
    years_by_model: Dict[str, set[int]] = defaultdict(set)

    for car in cars:
        models[car.make].add(car.model)
        years_by_model[f"{car.make}|{car.model}"].add(car.year)

    return {
        "makes": makes,
        "models": {make: sorted(model_set) for make, model_set in models.items()},
        "years_by_model": {
            key: sorted(years) for key, years in years_by_model.items()
        },
    }


def attach_dimensions(car: CarMeta) -> CarMeta:
    """Return a new CarMeta with width/height/aspect ratio filled if possible."""

    width: int | None = None
    height: int | None = None
    aspect: float | None = None

    try:
        with Image.open(car.path) as img:
            width, height = img.size
            if height:
                aspect = round(width / height, 4)
    except OSError:
        pass

    return CarMeta(
        id=car.id,
        path=car.path,
        make=car.make,
        model=car.model,
        year=car.year,
        attributes=car.attributes,
        thumb_path=car.thumb_path,
        width=width,
        height=height,
        aspect_ratio=aspect,
    )


def main() -> None:
    """Generate the index.json file."""

    if not DATA_DIR.exists():
        raise SystemExit("data directory is missing.")

    raw_cars = list(iter_car_meta(scan_images(DATA_DIR)))
    if not raw_cars:
        raise SystemExit("no parsable images were found.")

    cars = [attach_dimensions(car) for car in raw_cars]

    catalog = build_catalog(cars)
    payload = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": [
            {
                "id": car.id,
                "path": _to_relative(car.path),
                "thumb_path": str(Path("thumbs") / f"{car.path.stem}.jpg"),
                "make": car.make,
                "model": car.model,
                "year": car.year,
                "attributes": car.attributes,
                "width": car.width,
                "height": car.height,
                "aspect_ratio": car.aspect_ratio,
            }
            for car in cars
        ],
        "catalog": catalog,
    }

    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"generated: {OUTPUT_PATH}")


def _to_relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()

