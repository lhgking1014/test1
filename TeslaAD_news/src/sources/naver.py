from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Iterable, List

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


def fetch_naver_news(queries: Iterable[str], limit_per_query: int = 4) -> List[NewsItem]:
    items: List[NewsItem] = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        )
    }
    for query in queries:
        params = {"sm": "mtb_hty.top", "where": "m_news", "query": query}
        try:
            response = requests.get(
                "https://m.search.naver.com/search.naver",
                params=params,
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Failed to fetch Naver news for query %s: %s", query, exc)
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        for wrap in soup.select("div.news_wrap")[:limit_per_query]:
            title_el = wrap.select_one("a.news_tit, a.api_txt_lines")
            if not title_el:
                continue
            title = clean_text(title_el.get_text())
            link = title_el.get("href") or ""
            summary_el = wrap.select_one("div.dsc_wrap, a.api_txt_lines.dsc_txt")
            summary = summarise_text(summary_el.get_text(" ", strip=True) if summary_el else title, 180)
            source_el = wrap.select_one("span.info")
            source_name = clean_text(source_el.get_text()) if source_el else "네이버 뉴스"
            time_el = wrap.select_one("span.info_group span")
            published_at = parse_relative_time(clean_text(time_el.get_text()) if time_el else "")

            image_el = wrap.select_one("div.thumb img")
            image_url = image_el.get("data-src") if image_el and image_el.get("data-src") else None
            if not image_url and image_el:
                image_url = image_el.get("src")
            if not image_url:
                image_url = config.DEFAULT_IMAGE_URL

            combined = f"{title} {summary}"
            if is_stock_related(combined):
                continue
            if not is_autonomy_related(combined):
                continue

            items.append(
                NewsItem(
                    source=f"네이버 - {source_name}" if source_name else "네이버 뉴스",
                    title=title,
                    summary=summary,
                    url=link,
                    published_at=published_at,
                    image_url=image_url,
                    language="ko",
                )
            )
    return items


def parse_relative_time(text: str) -> str:
    now = datetime.now(config.KST)
    if not text:
        return now.isoformat()
    try:
        if "분 전" in text:
            minutes = int(text.replace("분 전", "").strip())
            return (now - timedelta(minutes=minutes)).isoformat()
        if "시간 전" in text:
            hours = int(text.replace("시간 전", "").strip())
            return (now - timedelta(hours=hours)).isoformat()
        if "일 전" in text:
            days = int(text.replace("일 전", "").strip())
            return (now - timedelta(days=days)).isoformat()
        if "어제" in text:
            return (now - timedelta(days=1)).isoformat()
        if "." in text and len(text) >= 8:
            parsed = datetime.strptime(text.replace(".", "-").strip("- "), "%Y-%m-%d")
            localized = config.KST.localize(parsed)
            return localized.isoformat()
    except Exception:
        logger.debug("Failed to parse Naver time string %s", text)
    return now.isoformat()
