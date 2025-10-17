from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List

from django.conf import settings

try:
    from google.cloud import vision
except ImportError:  # pragma: no cover
    vision = None  # type: ignore

logger = logging.getLogger(__name__)


def analyse_product_image(image_path: str) -> Dict:
    """Use Google Cloud Vision to extract product name suggestions."""

    if not vision:
        logger.warning("google-cloud-vision not installed; returning mock response")
        return _mock_response(Path(image_path).name)

    if not settings.GOOGLE_APPLICATION_CREDENTIALS:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS not configured; returning mock response")
        return _mock_response(Path(image_path).name)

    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    web_detection = client.web_detection(image=image).web_detection

    suggestions: List[Dict] = []
    if web_detection.web_entities:
        for entity in web_detection.web_entities[:5]:
            suggestions.append({"label": entity.description or "", "score": entity.score})

    best_guess = ""
    if web_detection.best_guess_labels:
        best_guess = web_detection.best_guess_labels[0].label or ""

    return {
        "best_guess": best_guess,
        "suggestions": suggestions,
    }


def _mock_response(filename: str) -> Dict:
    base_name = Path(filename).stem.replace("_", " ")
    return {
        "best_guess": base_name.title(),
        "suggestions": [
            {"label": f"{base_name.title()} 전통 공예품", "score": 0.42},
            {"label": base_name.title(), "score": 0.35},
        ],
    }

