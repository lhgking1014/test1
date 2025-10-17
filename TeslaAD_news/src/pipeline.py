from __future__ import annotations

import json
import logging
import re
from collections import OrderedDict
from dataclasses import asdict
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Iterable, List
from urllib.parse import quote_plus

from . import config, feedback, image_cache
from .models import NewsItem
from .sources.google import fetch_google_news
from .sources.naver import fetch_naver_news
from .utils import is_autonomy_related, translate_to_korean


logger = logging.getLogger(__name__)

SPLIT_SENTENCES = re.compile(r"(?<=[.!?])\s+|(?:\n|\r)+|-+")
SPLIT_PHRASES = re.compile(r"[,;]")


def get_item_datetime(item: NewsItem) -> datetime:
    try:
        dt = datetime.fromisoformat(item.published_at)
        if dt.tzinfo is None:
            return config.KST.localize(dt)
        return dt.astimezone(config.KST)
    except Exception:
        return datetime.now(config.KST)


def filter_recent(items: Iterable[NewsItem], hours: int) -> List[NewsItem]:
    cutoff = datetime.now(config.KST) - timedelta(hours=hours)
    return [item for item in items if get_item_datetime(item) >= cutoff]


def deduplicate(items: Iterable[NewsItem]) -> List[NewsItem]:
    unique: OrderedDict[str, NewsItem] = OrderedDict()
    for item in items:
        key = item.url or item.title
        if key not in unique:
            unique[key] = item
    return list(unique.values())


def translate_items(items: Iterable[NewsItem]) -> List[NewsItem]:
    translated: List[NewsItem] = []
    for item in items:
        translated_title = translate_to_korean(item.title)
        translated_summary = translate_to_korean(item.summary)
        raw_highlights = item.highlights or []
        translated_highlights = [translate_to_korean(point) for point in raw_highlights]
        if len(translated_highlights) < 2:
            translated_highlights = build_highlights(translated_summary)
        translated.append(
            NewsItem(
                source=item.source,
                title=translated_title,
                summary=translated_summary,
                url=item.url,
                published_at=item.published_at,
                image_url=item.image_url,
                language="ko",
                highlights=translated_highlights,
            )
        )
    return translated


def ensure_autonomy_focus(items: Iterable[NewsItem]) -> List[NewsItem]:
    focused: List[NewsItem] = []
    for item in items:
        combined = f"{item.title} {item.summary}"
        if is_autonomy_related(combined):
            focused.append(item)
    return focused


def build_highlights(text: str, max_points: int = 3) -> List[str]:
    if not text:
        return []

    cleaned = (
        text.replace("·", ".")
        .replace("•", ".")
        .replace("▶", ".")
    )
    candidates = [segment.strip(" -") for segment in SPLIT_SENTENCES.split(cleaned)]
    highlights: List[str] = []
    seen: set[str] = set()

    for segment in candidates:
        if not segment or len(segment) < 4:
            continue
        if segment in seen:
            continue
        seen.add(segment)
        highlights.append(segment[:160].rstrip())
        if len(highlights) >= max_points:
            break

    if len(highlights) < max_points:
        extras: List[str] = []
        for segment in candidates:
            for part in SPLIT_PHRASES.split(segment):
                part = part.strip()
                if len(part) < 6 or part in seen:
                    continue
                seen.add(part)
                extras.append(part[:160].rstrip())
        for part in extras:
            if len(highlights) >= max_points:
                break
            highlights.append(part)

    if len(highlights) < max_points:
        highlights.append("자세한 내용은 원문을 참고하세요.")

    return highlights[:max_points]


def string_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def filter_similar(items: Iterable[NewsItem], scores: dict[str, float]) -> List[NewsItem]:
    filtered: List[NewsItem] = []
    for item in items:
        keep = True
        for idx, existing in enumerate(filtered):
            title_sim = string_similarity(item.title, existing.title)
            summary_sim = string_similarity(item.summary, existing.summary)
            similarity = max(title_sim, summary_sim)
            if similarity >= config.SIMILARITY_THRESHOLD:
                if scores.get(item.url, 0.0) > scores.get(existing.url, 0.0):
                    filtered[idx] = item
                keep = False
                break
        if keep:
            filtered.append(item)
    return filtered


def fallback_image(title: str) -> str:
    keywords = " ".join(title.split()[:4]).strip()
    query = quote_plus(f"tesla autonomous driving {keywords}")
    return f"https://source.unsplash.com/featured/?{query}"


def collect_news() -> List[NewsItem]:
    google_feeds = [
        {
            "url": "https://news.google.com/rss/search?q=Tesla+autonomous+driving+OR+Autopilot+OR+FSD+OR+Robotaxi&hl=en-US&gl=US&ceid=US:en",
            "locale": "en",
        },
        {
            "url": "https://news.google.com/rss/search?q=%ED%85%8C%EC%8A%AC%EB%9D%BC+%EC%9E%90%EC%9C%A8%EC%A3%BC%ED%96%89+OR+%EB%A1%9C%EB%B3%B4%ED%83%9D%EC%8B%9C+OR+%EC%9E%90%EC%9C%A8%EC%9A%B4%EC%A0%84&hl=ko&gl=KR&ceid=KR:ko",
            "locale": "ko",
        },
    ]

    collected: List[NewsItem] = []
    collected.extend(fetch_google_news(google_feeds, limit_per_feed=12))
    collected.extend(fetch_naver_news(["테슬라 자유주행", "테슬라 로보택시"], limit_per_query=8))

    deduped = deduplicate(collected)
    focused = ensure_autonomy_focus(deduped)

    focused = [item for item in focused if not feedback.should_exclude(item.url)]
    scores = {item.url: feedback.score_article(item.title, item.summary) for item in focused}

    recent = filter_recent(focused, config.RECENT_HOURS)
    fallback_cutoff = datetime.now(config.KST) - timedelta(hours=config.RECENT_FALLBACK_HOURS)

    if len(recent) < config.MAX_ITEMS:
        extended = filter_recent(focused, config.RECENT_FALLBACK_HOURS)
        urls = {item.url for item in recent}
        for item in extended:
            if len(recent) >= config.MAX_ITEMS:
                break
            if item.url in urls or feedback.should_exclude(item.url):
                continue
            recent.append(item)
            urls.add(item.url)
            scores.setdefault(item.url, feedback.score_article(item.title, item.summary))

    if len(recent) < config.MAX_ITEMS:
        urls = {item.url for item in recent}
        for item in focused:
            if len(recent) >= config.MAX_ITEMS:
                break
            if item.url in urls or feedback.should_exclude(item.url):
                continue
            if get_item_datetime(item) < fallback_cutoff:
                continue
            recent.append(item)
            urls.add(item.url)
            scores.setdefault(item.url, feedback.score_article(item.title, item.summary))

    recent = [item for item in recent if get_item_datetime(item) >= fallback_cutoff]

    if len(recent) < config.MIN_ITEMS:
        logger.warning(
            "Only %d items found within the recent window (primary %d h / fallback %d h)",
            len(recent),
            config.RECENT_HOURS,
            config.RECENT_FALLBACK_HOURS,
        )

    recent = filter_similar(recent, scores)
    if len(recent) < config.MAX_ITEMS:
        used_urls = {item.url for item in recent}
        candidates = [
            item
            for item in focused
            if item.url not in used_urls and get_item_datetime(item) >= fallback_cutoff
        ]
        candidates.sort(
            key=lambda item: (scores.get(item.url, 0.0), get_item_datetime(item)),
            reverse=True,
        )
        for candidate in candidates:
            if len(recent) >= config.MAX_ITEMS:
                break
            duplicate = False
            for existing in recent:
                title_sim = string_similarity(candidate.title, existing.title)
                summary_sim = string_similarity(candidate.summary, existing.summary)
                if max(title_sim, summary_sim) >= config.SIMILARITY_THRESHOLD:
                    duplicate = True
                    break
            if duplicate:
                continue
            recent.append(candidate)
            used_urls.add(candidate.url)
    recent.sort(key=lambda item: (scores.get(item.url, 0.0), get_item_datetime(item)), reverse=True)

    top_items = recent[: config.MAX_ITEMS]
    enriched = enrich_items(top_items)
    translated = translate_items(enriched)
    image_cache.persist_cache()
    return translated


def write_news(items: List[NewsItem]) -> dict:
    payload = {
        "updated_at": datetime.now(config.KST).isoformat(),
        "items": [asdict(item) for item in items],
    }
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def enrich_items(items: Iterable[NewsItem]) -> List[NewsItem]:
    enriched: List[NewsItem] = []
    for item in items:
        article_data = image_cache.resolve_article_data(item.url)

        image_url = article_data.get("image") or item.image_url or fallback_image(item.title)

        raw_highlights = article_data.get("highlights") or item.highlights or build_highlights(item.summary)

        enriched.append(
            NewsItem(
                source=item.source,
                title=item.title,
                summary=item.summary,
                url=item.url,
                published_at=item.published_at,
                image_url=image_url,
                language=item.language,
                highlights=raw_highlights,
            )
        )
    return enriched
