from __future__ import annotations

import functools
import logging
import re
from html import unescape
from typing import Iterable

import requests

from . import config


logger = logging.getLogger(__name__)
TRANSLATE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"


def clean_text(value: str) -> str:
    if not value:
        return ""
    text = unescape(value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def summarise_text(text: str, limit: int = 160) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def translate_to_korean(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    try:
        translated = _translate_cached(text)
        return translated or text
    except Exception as exc:
        logger.debug("Translation failed: %s", exc)
        return text


@functools.lru_cache(maxsize=1024)
def _translate_cached(text: str) -> str | None:
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": "ko",
        "dt": "t",
        "q": text,
    }
    response = requests.get(TRANSLATE_ENDPOINT, params=params, timeout=10, headers={"User-Agent": config.USER_AGENT})
    response.raise_for_status()
    data = response.json()
    translated_segments = [segment[0] for segment in data[0] if segment and segment[0]]
    return "".join(translated_segments)


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def is_stock_related(text: str) -> bool:
    return contains_any(text, config.STOCK_KEYWORDS)


def is_autonomy_related(text: str) -> bool:
    return contains_any(text, config.AUTONOMY_KEYWORDS)


_IMG_REGEX = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)


def extract_image_url(html: str) -> str | None:
    if not html:
        return None
    match = _IMG_REGEX.search(html)
    if match:
        return match.group(1)
    return None
