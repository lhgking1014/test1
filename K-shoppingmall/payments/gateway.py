from __future__ import annotations

import secrets
from typing import Dict

from django.conf import settings

from .models import Payment


class PaymentGateway:
    """Mock gateway that validates payloads and stores payment records."""

    def process(self, order, method: str, payload: Dict) -> Dict:
        method = (method or "").lower()
        if method not in (Payment.Method.CARD, Payment.Method.NAVERPAY):
            return {"success": False, "message": "지원하지 않는 결제 수단입니다."}

        if method == Payment.Method.CARD:
            validation = self._validate_card_payload(payload)
            if not validation["valid"]:
                return {"success": False, "message": validation["message"]}

        transaction_id = self._generate_transaction_id(method)
        result = {
            "success": True,
            "transaction_id": transaction_id,
            "processor": settings.PAYMENT_SETTINGS.get(method.upper(), {}).get("provider", "mock"),
            "raw_response": {"payload": payload},
        }

        Payment.objects.update_or_create(
            order=order,
            defaults={
                "method": method,
                "amount": order.total_amount,
                "transaction_id": transaction_id,
                "processor": result["processor"],
                "raw_response": result["raw_response"],
            },
        )

        return result

    def _generate_transaction_id(self, method: str) -> str:
        prefix = settings.PAYMENT_SETTINGS.get(method.upper(), {}).get("success_prefix", method[:2].upper())
        return f"{prefix}-{secrets.token_hex(5).upper()}"

    def _validate_card_payload(self, payload: Dict) -> Dict:
        number = "".join(filter(str.isdigit, payload.get("card_number", "")))
        if len(number) < 13 or not self._luhn_check(number):
            return {"valid": False, "message": "카드 번호가 올바르지 않습니다."}
        if not payload.get("expiry_month") or not payload.get("expiry_year"):
            return {"valid": False, "message": "카드 유효기간을 입력해 주세요."}
        if not payload.get("cvc"):
            return {"valid": False, "message": "CVC 번호를 입력해 주세요."}
        return {"valid": True}

    @staticmethod
    def _luhn_check(number: str) -> bool:
        digits = [int(d) for d in number]
        checksum = 0
        parity = len(digits) % 2
        for idx, digit in enumerate(digits):
            if idx % 2 == parity:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        return checksum % 10 == 0

