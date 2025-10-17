from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from core.models import TimeStampedModel

User = get_user_model()


class UserProfile(TimeStampedModel):
    """Extended profile data for users."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    nickname = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=100, blank=True)
    marketing_opt_in = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Profile({self.user.email})"


class SavedPaymentMethod(TimeStampedModel):
    """Tokenised payment method store for quick checkout."""

    CARD = "card"
    NAVERPAY = "naverpay"
    PAYMENT_CHOICES = [(CARD, "Card"), (NAVERPAY, "Naver Pay")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_methods")
    method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    last4 = models.CharField(max_length=4, blank=True)
    provider_id = models.CharField(max_length=128)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def __str__(self) -> str:
        return f"{self.user.email} {self.method} {self.last4}"

