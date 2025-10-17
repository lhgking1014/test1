from __future__ import annotations

import secrets
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Product

DATA_DIR = Path(__file__).resolve().parents[3] / "data"


class Command(BaseCommand):
    help = "Import images from data/ directory as draft products"

    def handle(self, *args, **options):
        if not DATA_DIR.exists():
            self.stdout.write(self.style.ERROR("data directory not found"))
            return

        created = 0
        for image_path in DATA_DIR.glob("*.jpg"):
            slug = slugify(image_path.stem)[:50] or secrets.token_hex(4)
            product, is_created = Product.objects.get_or_create(slug=slug, defaults={"name": image_path.stem})
            if not is_created:
                continue
            with image_path.open("rb") as f:
                product.image.save(image_path.name, File(f), save=False)
            product.assign_initial_price()
            product.inventory = 10
            product.status = Product.Status.DRAFT
            product.save()
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Imported {created} products."))

