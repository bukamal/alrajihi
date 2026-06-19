# -*- coding: utf-8 -*-
from __future__ import annotations

from views.widgets.returns_widget import _ret_dec
from currency import currency


class ReturnSettlementComponent:
    """Refund/credit settlement boundary for return document tabs."""

    def __init__(self, host) -> None:
        self.host = host

    def data(self) -> dict:
        method = self.host.payment_method_combo.currentData() if hasattr(self.host, 'payment_method_combo') else 'credit_only'
        refund = '0'
        if method != 'credit_only' and hasattr(self.host, 'refund_spin'):
            refund = str(currency.convert(_ret_dec(self.host.refund_spin.value()), currency.get_display_currency(), currency.storage_currency()))
        return {
            'refund_amount': refund,
            'payment_method': method,
            'cashbox_id': self.host.cashbox_combo.currentData() if hasattr(self.host, 'cashbox_combo') else None,
            'bank_account_id': self.host.bank_combo.currentData() if hasattr(self.host, 'bank_combo') else None,
        }
