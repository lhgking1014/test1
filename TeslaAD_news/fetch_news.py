from __future__ import annotations

import logging

from src import config
from src.pipeline import collect_news, write_news


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    items = collect_news()
    payload = write_news(items)
    logging.info("Stored %d items to %s", len(payload["items"]), config.DATA_FILE)


if __name__ == "__main__":
    main()
