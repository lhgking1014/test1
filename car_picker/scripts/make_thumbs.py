"""Create resized thumbnails for the car image dataset."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
THUMB_DIR = ROOT / "thumbs"
MAX_SIZE = 1024


def ensure_thumb_dir() -> None:
    THUMB_DIR.mkdir(parents=True, exist_ok=True)


def build_thumb_path(image_path: Path) -> Path:
    return THUMB_DIR / f"{image_path.stem}.jpg"


def generate_thumb(image_path: Path) -> Path:
    thumb_path = build_thumb_path(image_path)
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        img.thumbnail((MAX_SIZE, MAX_SIZE))
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(thumb_path, format="JPEG", quality=88)
    return thumb_path


def iter_images(directory: Path) -> list[Path]:
    extensions = {".jpg", ".jpeg", ".png", ".webp"}
    return [
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in extensions
    ]


def main() -> None:
    ensure_thumb_dir()
    images = iter_images(DATA_DIR)
    if not images:
        raise SystemExit("no images found to process.")

    for image in images:
        generate_thumb(image)

    print("thumbnail generation complete.")


if __name__ == "__main__":
    main()

