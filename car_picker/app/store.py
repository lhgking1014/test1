"""Load and cache the indexed car metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Mapping, Optional

from .parser import CarMeta

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Catalog:
    """Lookup tables derived from the dataset."""

    makes: List[str]
    models_by_make: Mapping[str, List[str]]
    years_by_model: Mapping[str, List[int]]


@dataclass
class CarIndex:
    """Container for the dataset and catalog."""

    cars: List[CarMeta]
    catalog: Catalog


def load_index(path: Path) -> CarIndex:
    """Read index.json and return a CarIndex."""

    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items", [])

    cars: List[CarMeta] = []
    for item in items:
        image_path = Path(item["path"])
        if not image_path.is_absolute():
            image_path = ROOT / image_path

        thumb_path = item.get("thumb_path")
        thumb_abs: Optional[Path] = None
        if thumb_path:
            thumb_abs = Path(thumb_path)
            if not thumb_abs.is_absolute():
                thumb_abs = ROOT / thumb_abs

        cars.append(
            CarMeta(
                id=item["id"],
                path=image_path,
                make=item["make"],
                model=item["model"],
                year=int(item["year"]),
                attributes=list(item.get("attributes", [])),
                thumb_path=thumb_abs,
                width=item.get("width"),
                height=item.get("height"),
                aspect_ratio=item.get("aspect_ratio"),
            )
        )

    # Filter to images that likely show the entire car.
    filtered_cars = [car for car in cars if car.is_full_view()]
    if len(filtered_cars) < 10:
        filtered_cars = cars

    catalog_data = data.get("catalog", {})
    catalog = Catalog(
        makes=list(catalog_data.get("makes", [])),
        models_by_make={
            make: list(models) for make, models in catalog_data.get("models", {}).items()
        },
        years_by_model={
            key: [int(year) for year in years]
            for key, years in catalog_data.get("years_by_model", {}).items()
        },
    )

    return CarIndex(cars=filtered_cars, catalog=catalog)

