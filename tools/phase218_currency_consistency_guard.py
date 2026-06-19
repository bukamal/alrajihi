#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 218 currency consistency guard.

Protects the unified post-Phase-200 UI paths from reintroducing direct USD
assumptions. Database defaults/migrations may still mention USD; this guard only
covers display/editing modules that must honor the active display/base currency.
"""
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_CURRENCY_API = [
    "def storage_currency(self)",
    "def display_currency(self)",
    "def to_display(self, amount",
    "def from_display(self, amount",
    "def format_display_amount(self, amount",
    "def format_base_amount(self, amount",
]

UI_NO_DIRECT_USD = [
    "alrajhi_client/features/vouchers/components/voucher_payment.py",
    "alrajhi_client/features/vouchers/components/voucher_link.py",
    "alrajhi_client/features/pos/pos_line_model.py",
    "alrajhi_client/features/restaurant/restaurant_order_model.py",
    "alrajhi_client/views/restaurant/restaurant_pos_widget.py",
    "alrajhi_client/features/manufacturing/production_order_lifecycle_tab.py",
    "alrajhi_client/views/widgets/pos_widget.py",
    "alrajhi_client/views/widgets/cashboxes_widget.py",
]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    currency_py = text("alrajhi_client/currency.py")
    missing = [needle for needle in REQUIRED_CURRENCY_API if needle not in currency_py]
    if missing:
        raise AssertionError(f"currency.py missing unified currency helpers: {missing}")

    token_re = re.compile(r"(['\"])USD\1")
    offenders = []
    for rel in UI_NO_DIRECT_USD:
        src = text(rel)
        if token_re.search(src):
            offenders.append(rel)
    if offenders:
        raise AssertionError("Unified UI paths must use currency.storage_currency()/to_display()/from_display(), not direct USD literals: " + ", ".join(offenders))

    restaurant = text("alrajhi_client/views/restaurant/restaurant_pos_widget.py")
    required_restaurant = [
        "_display_money(balance.get('subtotal'",
        "_display_to_base_text(self.amount_edit.text()",
        "_base_to_display_text(remaining",
        "_display_to_base_text(self.discount_edit.text()",
        "_display_money(result.get('remaining'",
    ]
    missing_restaurant = [needle for needle in required_restaurant if needle not in restaurant]
    if missing_restaurant:
        raise AssertionError(f"Restaurant POS still has unaligned display/base currency paths: {missing_restaurant}")

    voucher_payment = text("alrajhi_client/features/vouchers/components/voucher_payment.py")
    for needle in ("currency.to_display", "currency.from_display", "currency.get_current_rate(currency.get_display_currency())"):
        if needle not in voucher_payment:
            raise AssertionError(f"VoucherPaymentPanel missing expected currency path: {needle}")

    print("phase218_currency_consistency_guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
