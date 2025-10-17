from __future__ import annotations

import json
import logging
import re
from collections import Counter
from datetime import datetime
from typing import Dict

from . import config


logger = logging.getLogger(__name__)

STATUS_OPTIONS = ["neutral", "high", "low"]
LABEL_MAP = {
    "neutral": None,  # no user selection yet
    "high": "High relevance",
    "low": "Low relevance",
}
LABEL_TO_STATUS = {label: status for status, label in LABEL_MAP.items() if label}

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9\uAC00-\uD7A3]{2,}")
STATUS_WEIGHTS = {
    "neutral": 0.0,
    "high": 1.5,
    "low": -1.5,
}
WEIGHT_CLAMP = 10.0
HISTORY_LIMIT = 200

_CACHE: dict | None = None


def _normalise(data: dict) -> dict:
    if not isinstance(data.get("token_weights"), dict):
        data["token_weights"] = {}
    if not isinstance(data.get("article_feedback"), dict):
        data["article_feedback"] = {}
    else:
        for record in data["article_feedback"].values():
            if not isinstance(record, dict):
                continue
            record.setdefault("reason", None)
    if not isinstance(data.get("history"), list):
        data["history"] = []
    else:
        for entry in data["history"]:
            if isinstance(entry, dict):
                entry.setdefault("reason", None)
    data.pop("weights", None)
    return data


def _ensure_loaded() -> dict:
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    path = config.FEEDBACK_FILE
    default = {
        "token_weights": {},
        "article_feedback": {},
        "history": [],
        "updated_at": None,
    }

    raw_text = None
    if path.exists():
        try:
            raw_text = path.read_text(encoding="utf-8")
            _CACHE = json.loads(raw_text)
        except Exception as exc:
            logger.warning("Failed to read feedback file, resetting: %s", exc)
            _CACHE = json.loads(json.dumps(default))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        raw_text = json.dumps(default, ensure_ascii=False, indent=2)
        path.write_text(raw_text, encoding="utf-8")
        _CACHE = json.loads(raw_text)

    _CACHE = _normalise(_CACHE)
    serialised = json.dumps(_CACHE, ensure_ascii=False, indent=2)
    if raw_text is None or raw_text != serialised:
        path.write_text(serialised, encoding="utf-8")

    return _CACHE


def _save() -> None:
    data = _normalise(_ensure_loaded())
    data["updated_at"] = datetime.now(config.KST).isoformat()
    config.FEEDBACK_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def tokenize(text: str) -> Counter:
    words = TOKEN_PATTERN.findall(text.lower())
    return Counter(words)


def get_article_feedback(url: str) -> dict:
    data = _ensure_loaded()
    record = data["article_feedback"].get(url)
    if not record:
        return {}
    label = LABEL_MAP.get(record.get("status", "neutral"))
    return {**record, "relevance": label}


def get_status(url: str) -> str:
    data = _ensure_loaded()
    record = data["article_feedback"].get(url)
    if not record:
        return "neutral"
    return record.get("status", "neutral")


def should_exclude(url: str) -> bool:
    return get_status(url) == "low"


def record_feedback(url: str, title: str, summary: str, label: str | None, reason: str | None = None) -> bool:
    if not label:
        return False
    status = LABEL_TO_STATUS.get(label)
    if status is None:
        logger.debug("Unknown relevance label %s", label)
        return False

    cleaned_reason = (reason or "").strip() or None
    if status != "low":
        cleaned_reason = None

    data = _ensure_loaded()
    existing = data["article_feedback"].get(url, {})
    previous_status = existing.get("status", "neutral")
    if previous_status == status:
        if status != "low":
            return False
        existing_reason = (existing.get("reason") or "").strip() or None
        if existing_reason == cleaned_reason:
            return False
    else:
        delta = STATUS_WEIGHTS[status] - STATUS_WEIGHTS.get(previous_status, 0.0)
        if abs(delta) > 0.0:
            tokens = tokenize(f"{title} {summary}")
            weights: Dict[str, float] = data["token_weights"]
            for token, count in tokens.items():
                weights[token] = _clamp(weights.get(token, 0.0) + delta * count)

    data["article_feedback"][url] = {
        "status": status,
        "title": title,
        "summary": summary,
        "timestamp": datetime.now(config.KST).isoformat(),
        "reason": cleaned_reason,
    }
    data["history"].append(
        {
            "url": url,
            "status": status,
            "timestamp": datetime.now(config.KST).isoformat(),
            "reason": cleaned_reason,
        }
    )
    if len(data["history"]) > HISTORY_LIMIT:
        data["history"] = data["history"][-HISTORY_LIMIT:]

    _save()
    return True


def score_article(title: str, summary: str) -> float:
    data = _ensure_loaded()
    weights: Dict[str, float] = data["token_weights"]
    tokens = tokenize(f"{title} {summary}")
    return sum(weights.get(token, 0.0) * count for token, count in tokens.items())


def _clamp(value: float) -> float:
    if value > WEIGHT_CLAMP:
        return WEIGHT_CLAMP
    if value < -WEIGHT_CLAMP:
        return -WEIGHT_CLAMP
    return value
