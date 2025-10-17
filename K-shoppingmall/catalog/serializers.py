from __future__ import annotations

from rest_framework import serializers

from .models import Product, ProductMedia


class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = ("id", "image", "alt_text")


class ProductSerializer(serializers.ModelSerializer):
    media = ProductMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "price",
            "inventory",
            "status",
            "tags",
            "ai_suggestions",
            "image",
            "media",
        )
        read_only_fields = ("ai_suggestions",)

