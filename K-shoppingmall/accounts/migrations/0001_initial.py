from __future__ import annotations

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("nickname", models.CharField(blank=True, max_length=50)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("address_line1", models.CharField(blank=True, max_length=255)),
                ("address_line2", models.CharField(blank=True, max_length=255)),
                ("postal_code", models.CharField(blank=True, max_length=10)),
                ("city", models.CharField(blank=True, max_length=100)),
                ("marketing_opt_in", models.BooleanField(default=False)),
                (
                    "user",
                    models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SavedPaymentMethod",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("method", models.CharField(choices=[("card", "Card"), ("naverpay", "Naver Pay")], max_length=20)),
                ("last4", models.CharField(blank=True, max_length=4)),
                ("provider_id", models.CharField(max_length=128)),
                ("is_default", models.BooleanField(default=False)),
                (
                    "user",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="payment_methods", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-is_default", "-created_at"],
            },
        ),
    ]

