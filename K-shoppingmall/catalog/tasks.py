from __future__ import annotations

import logging

from celery import shared_task
from django.conf import settings

from .integrations import google_vision
from .models import Product, VisionJob

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60, max_retries=5)
def run_vision_analysis(self, job_id: int) -> None:
    job = VisionJob.objects.select_related("product").get(id=job_id)
    product: Product = job.product
    if not product.image:
        job.mark_failed("No primary image available")
        return

    job.mark_processing()
    try:
        result = google_vision.analyse_product_image(product.image.path)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Vision analysis failed")
        job.mark_failed(str(exc))
        raise

    suggestions = result.get("suggestions", [])
    if suggestions:
        product.ai_suggestions = suggestions
        if not product.name:
            product.name = suggestions[0].get("label", "")
        if not product.description:
            product.description = "\n".join(s.get("description", "") for s in suggestions if s.get("description"))
        product.assign_initial_price()
        product.save()

    job.mark_completed(result)

