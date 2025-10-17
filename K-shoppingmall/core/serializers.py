from __future__ import annotations

from rest_framework import serializers


class ShippingPolicySerializer(serializers.Serializer):
    domestic_only = serializers.BooleanField()
    free_shipping_threshold = serializers.IntegerField()
    standard_fee = serializers.IntegerField()
    delivery_window_days = serializers.ListField(child=serializers.IntegerField(), min_length=2, max_length=2)
    return_window_days = serializers.IntegerField()

