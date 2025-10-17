from __future__ import annotations

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Cart",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("session_key", models.CharField(blank=True, db_index=True, max_length=64)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.CASCADE,
                        related_name="carts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("number", models.CharField(max_length=32, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("paid", "Paid"),
                            ("fulfilled", "Fulfilled"),
                            ("cancelled", "Cancelled"),
                            ("refunded", "Refunded"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("total_amount", models.PositiveIntegerField(default=0)),
                ("shipping_name", models.CharField(max_length=100)),
                ("shipping_phone", models.CharField(max_length=20)),
                ("shipping_address1", models.CharField(max_length=255)),
                ("shipping_address2", models.CharField(blank=True, max_length=255)),
                ("shipping_postal_code", models.CharField(max_length=10)),
                ("shipping_city", models.CharField(max_length=50)),
                ("shipping_request", models.CharField(blank=True, max_length=255)),
                ("shipped_at", models.DateTimeField(blank=True, null=True)),
                ("tracking_number", models.CharField(blank=True, max_length=64)),
                (
                    "user",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="orders", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="CartItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("cart", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="items", to="orders.cart")),
                ("product", models.ForeignKey(on_delete=models.deletion.CASCADE, to="catalog.product")),
            ],
            options={
                "unique_together": {("cart", "product")},
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("price", models.PositiveIntegerField()),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("order", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="items", to="orders.order")),
                ("product", models.ForeignKey(on_delete=models.deletion.PROTECT, to="catalog.product")),
            ],
        ),
    ]

