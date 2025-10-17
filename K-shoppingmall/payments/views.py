from __future__ import annotations

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView


class PaymentMethodsView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request):
        methods = [
            {
                'method': 'card',
                'label': '신용/체크카드 (Visa, Mastercard)',
                'provider': settings.PAYMENT_SETTINGS['CARD']['provider'],
            },
            {
                'method': 'naverpay',
                'label': '네이버페이',
                'provider': settings.PAYMENT_SETTINGS['NAVERPAY']['provider'],
            },
        ]
        return Response({'methods': methods})

