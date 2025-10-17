from __future__ import annotations

from django.urls import path

from .views import ProductDetailView, ProductListView

app_name = "catalog-api"

urlpatterns = [
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
]

