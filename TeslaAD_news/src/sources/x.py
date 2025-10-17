from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Iterable, List

import requests

from .. import config
from ..models import NewsItem
from ..utils import clean_text, is_autonomy_related, is_stock_related, summarise_text

logger = logging.getLogger(__name__)


def fetch_x_snippets(limit: int = 3) -> List[NewsItem]:
    since_date = (datetime.now(config.KST) - timedelta(days=2)).strftime("%Y-%m-%d")
    query = "(Tesla OR 테슬라) (autonomous driving OR Autopilot OR 자율주행 OR FSD OR Robotaxi)"
    endpoint = (
        "https://r.jina.ai/http://nitter.net/search"
        f"?f=tweets&q={requests.utils.quote(query)}&since={since_date}"
    )
    try:
        response = requests.get(endpoint, headers={"User-Agent": config.USER_AGENT}, timeout=20)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to fetch X snippets: %s", exc)
        return []

    snippets = _parse_markdown(response.text)
    posts: List[NewsItem] = []
    timestamp = datetime.now(config.KST)

    for snippet in snippets:
        combined = clean_text(snippet)
        if is_stock_related(combined):
            continue
        if not is_autonomy_related(combined):
            continue
        summary = summarise_text(combined, 200)
        title = summarise_text(combined, 80)
        posts.append(
            NewsItem(
                source="X (Nitter)",
                title=f"X : {title}",
                summary=summary,
                url=f"https://nitter.net/search?f=tweets&q={requests.utils.quote(title)}",
                published_at=timestamp.isoformat(),
                image_url=config.DEFAULT_IMAGE_URL,
                language="multi",
            )
        )
        timestamp -= timedelta(minutes=5)
        if len(posts) >= limit:
            break

    return posts


def _parse_markdown(markdown: str) -> List[str]:
    posts: List[str] = []
    current: List[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                posts.append(" ".join(current))
                current = []
            continue
        if line.startswith("Title:") or line.startswith("URL Source:") or line.startswith("Markdown Content:"):
            continue
        if line.startswith("Warning:") or line.startswith("[![") or line.startswith("[]"):
            continue
        if "http://nitter.net" in line or "https://nitter.net" in line:
            continue
        simplified = line.replace(",", "").replace(".", "")
        if simplified.isdigit():
            continue
        if all(ch in "-=_*" for ch in line):
            continue
        if line.lower() in {"gif", "video"}:
            continue
        current.append(line)

    if current:
        posts.append(" ".join(current))

    cleaned: List[str] = []
    seen = set()
    for post in posts:
        normalized = " ".join(post.split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(normalized)
    return cleaned
