import json
import logging
from collections import OrderedDict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from typing import Iterable, List, Sequence, Set
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET

import pytz
import requests
from bs4 import BeautifulSoup


KST = pytz.timezone("Asia/Seoul")
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "data" / "news.json"
MAX_ITEMS = 10
MIN_ITEMS = 5
MIN_NAVER_ITEMS = 1
X_SEARCH_WINDOW_DAYS = 2

AUTONOMY_KEYWORDS = [
    "autonomous driving",
    "autonomous vehicle",
    "autopilot",
    "full self-driving",
    "full self driving",
    "fsd",
    "self-driving",
    "self driving",
    "robotaxi",
    "robotaxis",
    "driverless",
    "tesla drive pilot",
    "로보택시",
    "자율주행",
    "자율 주행",
    "자율주행차",
    "자율주행 기능",
    "자율 운전",
    "자율운전",
    "오토파일럿",
    "완전자율주행",
    "완전 자율주행",
    "주행 보조",
    "주행보조",
    "운전자 보조",
    "운전자보조",
    "adas",
]

STOCK_KEYWORDS = [
    "stock",
    "stocks",
    "share price",
    "shares",
    "주가",
    "증시",
    "주식",
    "목표가",
    "target price",
    "valuation",
    "earnings",
    "실적",
    "수익",
    "주주",
    "dividend",
    "analyst",
    "downgrade",
    "업종",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/118.0.0.0 Safari/537.36"
)


@dataclass
class NewsItem:
    source: str
    title: str
    summary: str
    url: str
    published_at: str


def _combine_text(*parts: str) -> str:
    return " ".join(filter(None, (part.strip() for part in parts if part is not None)))


def _normalized(text: str) -> str:
    return unescape(text).lower()


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def is_stock_related(text: str) -> bool:
    return contains_any(text, STOCK_KEYWORDS)


def is_autonomy_related(text: str) -> bool:
    return contains_any(text, AUTONOMY_KEYWORDS)


def summarise(text: str, limit: int = 220) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "…"


def fetch_google_news(locale: str, url: str, limit: int = 5, require_autonomy: bool = False) -> List[NewsItem]:
    logging.info("Fetching Google News feed: %s", url)
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    items = []
    for item in root.findall(".//item")[:limit]:
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        description = unescape(item.findtext("description") or "")
        summary = summarise(BeautifulSoup(description, "html.parser").get_text(" ", strip=True))
        pub_date = item.findtext("pubDate") or ""
        published_at = parse_pub_date(pub_date)
        combined = _combine_text(title, summary)
        if is_stock_related(combined):
            continue
        if require_autonomy and not is_autonomy_related(combined):
            continue
        items.append(
            NewsItem(
                source=f"Google News ({locale})",
                title=title,
                summary=summary,
                url=link,
                published_at=published_at.isoformat(),
            )
        )
    return items


def parse_pub_date(raw: str) -> datetime:
    if not raw:
        return datetime.now(KST)
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(KST)
    except (TypeError, ValueError):
        return datetime.now(KST)


def fetch_naver_news(query: str, limit: int = 5, require_autonomy: bool = False) -> List[NewsItem]:
    url = "https://search.naver.com/search.naver"
    params = {"where": "news", "query": query, "sm": "tab_opt"}
    logging.info("Fetching Naver News search page for query: %s", query)
    response = requests.get(
        url,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items: List[NewsItem] = []
    for area in soup.select("div.news_area")[:limit]:
        title_el = area.select_one("a.news_tit")
        summary_el = area.select_one("a.api_txt_lines.dsc_txt_wrap")
        info_els = area.select("div.news_info > div.info_group > a.info, div.news_info > div.info_group > span.info")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        link = title_el.get("href", "").strip()
        summary = summarise(summary_el.get_text(" ", strip=True) if summary_el else "")
        published = extract_naver_published(info_els)
        combined = _combine_text(title, summary)
        if is_stock_related(combined):
            continue
        if require_autonomy and not is_autonomy_related(combined):
            continue
        items.append(
            NewsItem(
                source="Naver 뉴스",
                title=title,
                summary=summary,
                url=link,
                published_at=published.isoformat(),
            )
        )
    return items


def extract_naver_published(info_elements: Iterable) -> datetime:
    now = datetime.now(KST)
    for el in info_elements:
        text = el.get_text(strip=True)
        parsed = parse_naver_time(text, now)
        if parsed:
            return parsed
    return now


def parse_naver_time(text: str, reference: datetime) -> datetime | None:
    if not text:
        return None
    text = text.strip()
    if "분 전" in text:
        try:
            minutes = int(text.replace("분 전", "").strip())
            return reference - timedelta(minutes=minutes)
        except ValueError:
            return None
    if "시간 전" in text:
        try:
            hours = int(text.replace("시간 전", "").strip())
            return reference - timedelta(hours=hours)
        except ValueError:
            return None
    if "일 전" in text:
        try:
            days = int(text.replace("일 전", "").strip())
            return reference - timedelta(days=days)
        except ValueError:
            return None
    if text == "어제":
        return (reference - timedelta(days=1)).replace(second=0, microsecond=0)

    normalized = text.replace("오전", "AM").replace("오후", "PM").strip()
    for fmt in ("%Y.%m.%d.", "%Y.%m.%d. %p %I:%M"):
        try:
            naive = datetime.strptime(normalized, fmt)
            if "%p" in fmt:
                return KST.localize(naive)
            return KST.localize(naive)
        except ValueError:
            continue
    return None


def deduplicate(items: Iterable[NewsItem]) -> List[NewsItem]:
    unique = OrderedDict()
    for item in items:
        key = item.url or item.title
        if key and key not in unique:
            unique[key] = item
    return list(unique.values())


def prioritize_autonomy(items: List[NewsItem]) -> List[NewsItem]:
    filtered: List[NewsItem] = []
    autonomy: List[NewsItem] = []
    for item in items:
        combined = _combine_text(item.title, item.summary)
        if is_stock_related(combined):
            continue
        filtered.append(item)
        if is_autonomy_related(combined):
            autonomy.append(item)
    non_autonomy = [item for item in filtered if item not in autonomy]
    return autonomy + non_autonomy


def ensure_naver_presence(items: List[NewsItem], naver_candidates: Iterable[NewsItem]) -> List[NewsItem]:
    if any("Naver" in item.source for item in items):
        return items
    for candidate in naver_candidates:
        combined = _combine_text(candidate.title, candidate.summary)
        if is_stock_related(combined):
            continue
        if not is_autonomy_related(combined):
            continue
        updated = list(items)
        if len(updated) >= MAX_ITEMS:
            updated.pop()
        updated.append(candidate)
        return updated
    return items


def fetch_x_posts(limit: int = 3) -> List[NewsItem]:
    since_date = (datetime.now(KST) - timedelta(days=X_SEARCH_WINDOW_DAYS)).strftime("%Y-%m-%d")
    query = "(Tesla OR 테슬라) (autonomous driving OR Autopilot OR 자율주행 OR FSD)"
    endpoint = (
        "https://r.jina.ai/http://nitter.net/search"
        f"?f=tweets&q={quote_plus(query)}&since={since_date}"
    )
    logging.info("Fetching X posts via Nitter bridge: %s", endpoint)
    try:
        response = requests.get(endpoint, headers={"User-Agent": USER_AGENT}, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        logging.warning("Failed to fetch X posts: %s", exc)
        return []

    snippets = parse_nitter_markdown(response.text)
    logging.info("Parsed %d X snippets", len(snippets))
    posts: List[NewsItem] = []
    timestamp = datetime.now(KST)
    for snippet in snippets:
        combined = _combine_text(snippet)
        if is_stock_related(combined):
            continue
        if not is_autonomy_related(combined):
            continue
        title_excerpt = summarise(snippet, 80)
        summary_text = summarise(snippet, 200)
        search_link = f"https://nitter.net/search?f=tweets&q={quote_plus(title_excerpt)}"
        posts.append(
            NewsItem(
                source="X (via Nitter)",
                title=f"X: {title_excerpt}",
                summary=summary_text,
                url=search_link,
                published_at=timestamp.isoformat(),
            )
        )
        if len(posts) >= limit:
            break
        timestamp -= timedelta(minutes=5)
    return posts


def parse_nitter_markdown(markdown: str) -> List[str]:
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
        if line.startswith("Warning:"):
            continue
        if line.startswith("[![") and "](" in line:
            continue
        if line.startswith("[]"):
            continue
        if "| nitter" in line:
            continue
        if line.startswith("http://nitter.net") or line.startswith("https://nitter.net"):
            continue
        if line.startswith("* "):
            continue
        simplified = line.replace(",", "").replace(".", "")
        if simplified.isdigit():
            continue
        if all(ch in "-=_*" for ch in line):
            continue
        if line in {"GIF", "Video"}:
            continue
        current.append(line)
    if current:
        posts.append(" ".join(current))

    cleaned: List[str] = []
    seen = set()
    for post in posts:
        normalized = " ".join(post.split())
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(normalized)
    return cleaned


def ensure_data_directory() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_item_datetime(item: NewsItem) -> datetime:
    try:
        dt = datetime.fromisoformat(item.published_at)
    except (ValueError, TypeError, AttributeError):
        return datetime.now(KST)
    if dt.tzinfo is None:
        return KST.localize(dt)
    return dt.astimezone(KST)


def filter_recent_items(items: Iterable[NewsItem], hours: int = 24) -> List[NewsItem]:
    cutoff = datetime.now(KST) - timedelta(hours=hours)
    recent = []
    for item in items:
        if get_item_datetime(item) >= cutoff:
            recent.append(item)
    return recent


def write_news(items: List[NewsItem]) -> dict:
    ensure_data_directory()
    payload = {
        "updated_at": datetime.now(KST).isoformat(),
        "items": [asdict(item) for item in items],
    }
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    items = collect_news()
    write_news(items)
    logging.info("Stored %d news items to %s", len(items), DATA_PATH)


def collect_news(
    exclude_keys: Sequence[str] | None = None,
    initial_hours: int = 24,
    max_hours: int = 72,
) -> List[NewsItem]:
    excluded: Set[str] = set(filter(None, exclude_keys or []))
    google_feeds = [
        {
            "locale": "KR",
            "query": "테슬라 자율주행 OR 오토파일럿",
            "hl": "ko",
            "gl": "KR",
            "ceid": "KR:ko",
        },
        {
            "locale": "US",
            "query": 'Tesla "autonomous driving" OR Autopilot OR FSD',
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en",
        },
    ]

    collected: List[NewsItem] = []
    for feed in google_feeds:
        encoded_query = quote_plus(feed["query"])
        url = (
            f"https://news.google.com/rss/search?q={encoded_query}"
            f"&hl={feed['hl']}&gl={feed['gl']}&ceid={feed['ceid']}"
        )
        collected.extend(fetch_google_news(feed["locale"], url))

    naver_queries = ["테슬라 자율주행", "테슬라 오토파일럿", "테슬라 FSD"]
    naver_items: List[NewsItem] = []
    for query in naver_queries:
        naver_items.extend(fetch_naver_news(query, limit=3, require_autonomy=True))
    if len(naver_items) < MIN_NAVER_ITEMS:
        backup = fetch_naver_news("테슬라 자율주행", limit=4, require_autonomy=False)
        for item in backup:
            if item not in naver_items:
                naver_items.append(item)
    naver_site_feed = fetch_google_news(
        "KR",
        "https://news.google.com/rss/search?q=site:naver.com+%ED%85%8C%EC%8A%AC%EB%9D%BC+%EC%9E%90%EC%9C%A8%EC%A3%BC%ED%96%89&hl=ko&gl=KR&ceid=KR:ko",
        require_autonomy=True,
    )
    for item in naver_site_feed:
        item.source = "Naver (via Google)"
    naver_items.extend(naver_site_feed)
    recent_naver_items = filter_recent_items(naver_items, hours=initial_hours)
    if not recent_naver_items:
        logging.warning("No Naver news items found within the selected recency window.")
    else:
        logging.info(
            "Keeping %d Naver items from the past %d hours",
            len(recent_naver_items),
            initial_hours,
        )

    collected.extend(naver_items)

    x_posts = fetch_x_posts(limit=3)
    collected.extend(x_posts)

    deduped = deduplicate(collected)
    deduped.sort(key=get_item_datetime, reverse=True)
    prioritized = prioritize_autonomy(deduped)

    current_hours = max(1, initial_hours)
    max_hours = max(current_hours, max_hours)

    def pick_naver_candidates(window_hours: int) -> List[NewsItem]:
        scoped = filter_recent_items(naver_items, hours=window_hours)
        if scoped:
            return scoped
        return naver_items

    while True:
        scoped_items = filter_recent_items(prioritized, hours=current_hours)
        if not scoped_items:
            scoped_items = prioritized

        naver_candidates = pick_naver_candidates(current_hours)
        ensured = ensure_naver_presence(scoped_items, naver_candidates)
        filtered = [
            item
            for item in ensured
            if (item.url or item.title) not in excluded
        ]
        trimmed = filtered[:MAX_ITEMS]

        if len(trimmed) >= MIN_ITEMS or current_hours >= max_hours:
            if len(trimmed) < MIN_ITEMS:
                logging.warning(
                    "Only %d news items available after excluding low relevance items (minimum expected: %d)",
                    len(trimmed),
                    MIN_ITEMS,
                )
            return trimmed

        next_window = min(current_hours + 12, max_hours)
        logging.info(
            "Expanding news window to %d hours to replace excluded items.",
            next_window,
        )
        current_hours = next_window


if __name__ == "__main__":
    main()
