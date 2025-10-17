from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("method", models.CharField(choices=[("card", "Card"), ("naverpay", "Naver Pay")], max_length=20)),
                ("amount", models.PositiveIntegerField()),
                ("transaction_id", models.CharField(max_length=64, unique=True)),
                ("processor", models.CharField(max_length=50)),
                ("status", models.CharField(choices=[("approved", "Approved"), ("failed", "Failed"), ("refunded", "Refunded")], default="approved", max_length=20)),
                ("raw_response", models.JSONField(blank=True, null=True)),
                ("order", models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="payment", to="orders.order")),
            ],
        ),
    ]

