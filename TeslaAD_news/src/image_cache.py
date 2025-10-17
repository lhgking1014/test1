
from __future__ import annotations

import json
import logging
import re
from html import unescape
from typing import Any, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from . import config


logger = logging.getLogger(__name__)
_cache: dict[str, dict[str, Any]] = {}
_dirty = False
_loaded = False
TARGET_REGEX = re.compile(r"\"(?:targetUrl|canonicalUrl)\"\s*:\s*\"([^\"]+)\"")


def _load_cache() -> None:
    global _loaded, _cache
    if _loaded:
        return
    if config.IMAGE_CACHE_FILE.exists():
        try:
            _cache = json.loads(config.IMAGE_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("Failed to read article cache, resetting.")
            _cache = {}
    _loaded = True


def _save_cache() -> None:
    config.IMAGE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.IMAGE_CACHE_FILE.write_text(
        json.dumps(_cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def persist_cache() -> None:
    global _dirty
    if _dirty:
        _save_cache()
        _dirty = False


def resolve_article_data(url: str) -> dict[str, Any]:
    global _dirty
    _load_cache()
    if url in _cache:
        entry = _cache[url]
        if isinstance(entry, str):
            entry = {"image": entry, "highlights": []}
            _cache[url] = entry
            _dirty = True
        return entry

    data = _fetch_article_data(url)
    _cache[url] = data
    _dirty = True
    return data


def resolve_image(url: str) -> Optional[str]:
    return resolve_article_data(url).get("image")


def _fetch_article_data(url: str, depth: int = 0) -> dict[str, Any]:
    data: dict[str, Any] = {"image": None, "highlights": []}
    if depth > 2:
        return data

    try:
        response = requests.get(url, headers={"User-Agent": config.USER_AGENT}, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        logger.debug("Failed to fetch article (%s): %s", url, exc)
        return data

    soup = BeautifulSoup(response.text, "html.parser")
    final_url = response.url

    image = _extract_image(soup, final_url)
    highlights = _extract_highlights(soup)

    if not image or len(highlights) < 2:
        target_url = _extract_target_url(response.text, soup) or final_url
        if target_url != final_url:
            nested = _fetch_article_data(target_url, depth + 1)
            image = image or nested.get("image")
            if len(highlights) < len(nested.get("highlights", [])):
                highlights = nested.get("highlights", highlights)

    data["image"] = image
    data["highlights"] = highlights
    return data


def _extract_target_url(raw_text: str, soup: BeautifulSoup) -> Optional[str]:
    link = soup.find("meta", attrs={"property": "og:url"})
    if link and link.get("content"):
        candidate = unescape(link["content"].strip())
        if candidate.startswith("http"):
            return candidate

    link_tag = soup.find("link", attrs={"rel": "canonical"})
    if link_tag and link_tag.get("href"):
        candidate = unescape(link_tag["href"].strip())
        if candidate.startswith("http"):
            return candidate

    match = TARGET_REGEX.search(raw_text)
    if match:
        candidate = unescape(match.group(1))
        if candidate.startswith("http"):
            return candidate

    button = soup.select_one("a[data-n-href]")
    if button and button.get("data-n-href"):
        candidate = urljoin("https://news.google.com", button["data-n-href"].strip())
        if candidate.startswith("http"):
            return candidate

    return None


def _extract_image(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    meta_checks = [
        ("property", "og:image"),
        ("property", "og:image:url"),
        ("property", "og:image:secure_url"),
        ("name", "twitter:image"),
        ("property", "twitter:image"),
        ("itemprop", "image"),
    ]
    for attr, value in meta_checks:
        meta = soup.find("meta", attrs={attr: value})
        if meta and meta.get("content"):
            candidate = urljoin(base_url, meta["content"].strip())
            if _looks_like_image(candidate):
                return candidate

    link = soup.find("link", attrs={"rel": "image_src"})
    if link and link.get("href"):
        candidate = urljoin(base_url, link["href"].strip())
        if _looks_like_image(candidate):
            return candidate

    img = soup.find("img")
    if img and img.get("src"):
        candidate = urljoin(base_url, img["src"].strip())
        if _looks_like_image(candidate):
            return candidate

    return None


def _looks_like_image(url: str) -> bool:
    if not url.startswith("http"):
        return False
    return any(url.lower().split("?")[0].endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"))


def _extract_highlights(soup: BeautifulSoup) -> List[str]:
    highlights: List[str] = []
    seen = set()

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        value = meta_desc["content"].strip()
        if len(value) > 40:
            seen.add(value)
            highlights.append(value)

    for tag in soup.select("article p, article li, p, li"):
        text = tag.get_text(" ", strip=True)
        if not text or len(text) < 60:
            continue
        if text in seen:
            continue
        seen.add(text)
        highlights.append(text)
        if len(highlights) >= 5:
            break

    return highlights[:5]
