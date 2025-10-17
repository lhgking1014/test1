from __future__ import annotations

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ShippingPolicySerializer


class ShippingPolicyView(APIView):
    """Return current shipping policy."""

    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request):
        serializer = ShippingPolicySerializer(settings.SHIPPING_POLICY)
        return Response(serializer.data)

