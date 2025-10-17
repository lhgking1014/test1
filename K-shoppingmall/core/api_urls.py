from __future__ import annotations

from django.urls import path

from .views import ShippingPolicyView

app_name = "core-api"

urlpatterns = [
    path("shipping-policy/", ShippingPolicyView.as_view(), name="shipping-policy"),
]

