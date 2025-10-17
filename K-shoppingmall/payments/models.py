from __future__ import annotations

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from orders.models import Order


class Payment(TimeStampedModel):
    class Method(models.TextChoices):
        CARD = "card", "Card"
        NAVERPAY = "naverpay", "Naver Pay"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=20, choices=Method.choices)
    amount = models.PositiveIntegerField()
    transaction_id = models.CharField(max_length=64, unique=True)
    processor = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=[("approved", "Approved"), ("failed", "Failed"), ("refunded", "Refunded")],
        default="approved",
    )
    raw_response = models.JSONField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.order.number} {self.method} {self.transaction_id}"

