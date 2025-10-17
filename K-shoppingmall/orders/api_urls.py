from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CartViewSet, CheckoutView

app_name = "orders-api"

router = DefaultRouter()
router.register("cart", CartViewSet, basename="cart")

urlpatterns = router.urls + [
    path("checkout/", CheckoutView.as_view(), name="checkout"),
]

