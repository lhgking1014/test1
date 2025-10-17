import atexit
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, render_template

from fetch_news import DATA_PATH, KST, collect_news, ensure_data_directory, write_news


logger = logging.getLogger(__name__)
app = Flask(__name__)
_scheduler: BackgroundScheduler | None = None


def _refresh_news() -> Dict[str, Any]:
    logger.info("Refreshing Tesla news cache")
    items = collect_news()
    payload = write_news(items)
    return payload


def load_news() -> Dict[str, Any]:
    ensure_data_directory()
    if DATA_PATH.exists():
        try:
            return json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Cached news file is corrupted; regenerating.")
    refreshed = _refresh_news()
    return refreshed


@app.route("/")
def index():
    data = load_news()
    return render_template("index.html", updated_at=data["updated_at"], items=data["items"])


@app.route("/api/news")
def news():
    return jsonify(load_news())


def _start_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        return
    _scheduler = BackgroundScheduler(timezone=KST)
    _scheduler.add_job(_refresh_news, trigger="cron", hour=7, minute=0)
    _scheduler.start()
    atexit.register(lambda: _scheduler and _scheduler.shutdown(wait=False))


def create_app() -> Flask:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_news()  # ensure cache is ready on boot
    _start_scheduler()
    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)
