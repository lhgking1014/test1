from __future__ import annotations

import secrets

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from .models import Product


@receiver(pre_save, sender=Product)
def ensure_slug(sender, instance: Product, **kwargs):
    if not instance.slug:
        base_slug = slugify(instance.name) or secrets.token_hex(4)
        slug = base_slug
        counter = 1
        while Product.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        instance.slug = slug
    if not instance.price:
        instance.assign_initial_price()

