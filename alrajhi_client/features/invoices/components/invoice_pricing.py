# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal


class InvoicePricingEngine:
    """Pricing boundary for subtotal/discount/tax/final invoice totals."""

    def __init__(self, host) -> None:
        self.host = host

    def recalculate(self) -> None:
        if hasattr(self.host, 'update_total_display'):
            self.host.update_total_display()

    def summary(self) -> dict:
        return {
            'subtotal': getattr(self.host, 'total_before_discount', Decimal('0')),
            'discount': getattr(self.host, 'discount_amount', Decimal('0')),
            'total': getattr(self.host, 'total_after_discount', Decimal('0')),
        }
