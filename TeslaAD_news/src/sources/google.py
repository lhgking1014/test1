from __future__ import annotations

import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Iterable, List
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

from .. import config
from ..models import NewsItem
from ..utils import (
    clean_text,
    extract_image_url,
    is_autonomy_related,
    is_stock_related,
    summarise_text,
)

logger = logging.getLogger(__name__)


def fetch_google_news(feeds: Iterable[dict], limit_per_feed: int = 6) -> List[NewsItem]:
    items: List[NewsItem] = []
    for feed in feeds:
        url = feed["url"]
        try:
            response = requests.get(url, headers={"User-Agent": config.USER_AGENT}, timeout=20)
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Failed to fetch Google News feed %s: %s", url, exc)
            continue

        root = ET.fromstring(response.content)
        for entry in root.findall(".//item")[:limit_per_feed]:
            title = clean_text(entry.findtext("title") or "")
            link = entry.findtext("link") or ""
            description_raw = entry.findtext("description") or ""
            desc_soup = BeautifulSoup(description_raw, "html.parser")
            anchor = desc_soup.find("a", href=True)
            if anchor and anchor.get("href"):
                link = anchor["href"].strip()
            img_tag = desc_soup.find("img", src=True)
            image_url = img_tag["src"].strip() if img_tag else extract_image_url(description_raw)
            summary_html = desc_soup.get_text(" ", strip=True)
            summary = summarise_text(summary_html, 180)
            published_raw = entry.findtext("pubDate") or ""
            try:
                published_dt = parsedate_to_datetime(published_raw)
                published_at = published_dt.astimezone(config.KST).isoformat()
            except Exception:
                published_at = datetime.now(config.KST).isoformat()

            combined = f"{title} {summary}"
            if is_stock_related(combined):
                continue
            if not is_autonomy_related(combined):
                continue

            items.append(
                NewsItem(
                    source="Google 뉴스",
                    title=title,
                    summary=summary,
                    url=link,
                    published_at=published_at,
                    image_url=image_url,
                    language=feed.get("locale"),
                )
            )
    return items
