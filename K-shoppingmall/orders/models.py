from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from catalog.models import Product
from core.models import TimeStampedModel


class Cart(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carts",
        null=True,
        blank=True,
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"Cart({self.user or self.session_key})"

    @property
    def total_amount(self) -> Decimal:
        return sum((item.subtotal for item in self.items.all()), Decimal("0"))


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product")

    @property
    def subtotal(self) -> Decimal:
        return Decimal(self.product.price) * self.quantity


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FULFILLED = "fulfilled", "Fulfilled"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    number = models.CharField(max_length=32, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_amount = models.PositiveIntegerField(default=0)
    shipping_name = models.CharField(max_length=100)
    shipping_phone = models.CharField(max_length=20)
    shipping_address1 = models.CharField(max_length=255)
    shipping_address2 = models.CharField(max_length=255, blank=True)
    shipping_postal_code = models.CharField(max_length=10)
    shipping_city = models.CharField(max_length=50)
    shipping_request = models.CharField(max_length=255, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    tracking_number = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def mark_shipped(self, tracking_number: str) -> None:
        self.status = Order.Status.FULFILLED
        self.tracking_number = tracking_number
        self.shipped_at = timezone.now()
        self.save(update_fields=["status", "tracking_number", "shipped_at", "updated_at"])


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self) -> int:
        return self.price * self.quantity

