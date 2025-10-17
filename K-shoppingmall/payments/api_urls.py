from __future__ import annotations

from django.urls import path

from .views import PaymentMethodsView

app_name = "payments-api"

urlpatterns = [
    path("methods/", PaymentMethodsView.as_view(), name="payment-methods"),
]

