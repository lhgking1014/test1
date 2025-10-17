from __future__ import annotations

from pathlib import Path

import pytz


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "news.json"
IMAGE_CACHE_FILE = DATA_DIR / "image_cache.json"
ARTICLE_CACHE_FILE = IMAGE_CACHE_FILE  # backwards compatibility for cache
FEEDBACK_FILE = BASE_DIR / "feedback" / "relevance.json"

KST = pytz.timezone("Asia/Seoul")
MAX_ITEMS = 12
MIN_ITEMS = 8
RECENT_HOURS = 24
RECENT_FALLBACK_HOURS = 48
SIMILARITY_THRESHOLD = 0.82

DEFAULT_IMAGE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/e/e8/Tesla_logo.png"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
)

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
    "자율주행",
    "자율 주행",
    "자율운전",
    "완전자율주행",
    "오토파일럿",
    "로보택시",
    "주행 보조",
    "ADAS",
]

STOCK_KEYWORDS = [
    "stock",
    "stocks",
    "share price",
    "shares",
    "target price",
    "valuation",
    "earnings",
    "주가",
    "증시",
    "주식",
    "목표가",
    "실적",
    "수익",
    "주주",
]
