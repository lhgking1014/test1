from __future__ import annotations

import secrets


def generate_order_number() -> str:
    return secrets.token_hex(6).upper()

