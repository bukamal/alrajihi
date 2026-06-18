# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal


class InvoicePaymentsComponent:
    """Payment boundary for invoice document tabs."""

    def __init__(self, host) -> None:
        self.host = host

    def paid_amount(self) -> Decimal:
        try:
            return Decimal(str(self.host.paid_spin.value()))
        except Exception:
            return Decimal('0')

    def set_full_payment(self) -> None:
        if hasattr(self.host, 'set_paid_full'):
            self.host.set_paid_full()

    def set_deferred(self) -> None:
        if hasattr(self.host, 'set_paid_zero'):
            self.host.set_paid_zero()
