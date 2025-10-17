from __future__ import annotations

from rest_framework import serializers

from catalog.models import Product
from catalog.serializers import ProductSerializer
from .models import Cart, CartItem, Order, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source="product", write_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ("id", "product", "product_id", "quantity", "subtotal")
        read_only_fields = ("subtotal",)

    def get_subtotal(self, obj: CartItem) -> int:
        return int(obj.subtotal)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ("id", "user", "session_key", "is_active", "items", "total_amount")
        read_only_fields = ("user", "session_key", "is_active", "total_amount")

    def get_total_amount(self, obj: Cart) -> int:
        return int(obj.total_amount)


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ("id", "product", "price", "quantity", "subtotal")
        read_only_fields = ("subtotal",)

    def get_subtotal(self, obj: OrderItem) -> int:
        return obj.subtotal


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "number",
            "status",
            "total_amount",
            "shipping_name",
            "shipping_phone",
            "shipping_address1",
            "shipping_address2",
            "shipping_postal_code",
            "shipping_city",
            "shipping_request",
            "tracking_number",
            "items",
            "created_at",
        )
        read_only_fields = ("number", "status", "total_amount", "tracking_number", "created_at")

    def get_total_amount(self, obj: Order) -> int:
        return obj.total_amount

