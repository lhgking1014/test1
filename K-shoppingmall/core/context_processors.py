from __future__ import annotations

from django.conf import settings


def global_settings(request):
    """Expose project-wide settings to templates."""

    return {
        "SHIPPING_POLICY": settings.SHIPPING_POLICY,
        "PAYMENT_SETTINGS": settings.PAYMENT_SETTINGS,
    }

