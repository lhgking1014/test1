from __future__ import annotations

import random

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel


def product_image_upload_to(instance, filename) -> str:
    return f"products/{instance.slug}/{filename}"


class Product(TimeStampedModel):
    """Primary product information."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        ACTIVE = "active", _("Active")
        HIDDEN = "hidden", _("Hidden")

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=product_image_upload_to, blank=True, null=True)
    price = models.PositiveIntegerField(default=0)
    inventory = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    tags = models.JSONField(default=list, blank=True)
    ai_suggestions = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def assign_initial_price(self) -> None:
        if not self.price:
            self.price = random.randrange(10000, 100001, 1000)


class ProductMedia(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="media")
    image = models.ImageField(upload_to=product_image_upload_to)
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"{self.product.name} media"


class VisionJob(TimeStampedModel):
    """Track Google Vision processing for product images."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="vision_jobs")
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    response_payload = models.JSONField(blank=True, null=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def mark_processing(self):
        self.status = "processing"
        self.save(update_fields=["status", "updated_at"])

    def mark_completed(self, data: dict):
        self.status = "completed"
        self.response_payload = data
        self.save(update_fields=["status", "response_payload", "updated_at"])

    def mark_failed(self, message: str):
        self.status = "failed"
        self.error_message = message
        self.save(update_fields=["status", "error_message", "updated_at"])

