from __future__ import annotations

from django.db import migrations, models
import catalog.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField(blank=True)),
                ("image", models.ImageField(blank=True, null=True, upload_to=catalog.models.product_image_upload_to)),
                ("price", models.PositiveIntegerField(default=0)),
                ("inventory", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("active", "Active"), ("hidden", "Hidden")], default="draft", max_length=20)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("ai_suggestions", models.JSONField(blank=True, default=list)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="VisionJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=20)),
                ("response_payload", models.JSONField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True)),
                ("product", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="vision_jobs", to="catalog.product")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ProductMedia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("image", models.ImageField(upload_to=catalog.models.product_image_upload_to)),
                ("alt_text", models.CharField(blank=True, max_length=255)),
                ("product", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="media", to="catalog.product")),
            ],
        ),
    ]

