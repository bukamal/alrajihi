# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal


class InvoiceHeaderComponent:
    """Document-tab header boundary for invoice party/date/reference/warehouse state."""

    def __init__(self, host) -> None:
        self.host = host

    def data(self) -> dict:
        return {
            'entity_id': getattr(self.host, 'selected_entity_id', None),
            'entity_text': self.host.entity_search.text().strip() if hasattr(self.host, 'entity_search') else '',
            'date': self.host.date_edit.date().toString('yyyy-MM-dd') if hasattr(self.host, 'date_edit') else '',
            'reference': self.host.ref_edit.text().strip() if hasattr(self.host, 'ref_edit') else '',
            'warehouse_id': self.host._selected_warehouse_id() if hasattr(self.host, '_selected_warehouse_id') else None,
            'notes': self.host.notes_edit.toPlainText().strip() if hasattr(self.host, 'notes_edit') else '',
        }


class InvoiceLinesComponent:
    """Unit-aware invoice lines boundary for sales, purchases, returns, POS, and restaurant checkout."""

    def __init__(self, host) -> None:
        self.host = host

    @property
    def model(self):
        return getattr(self.host, 'lines_model', None)

    def lines(self) -> list[dict]:
        model = self.model
        return list(getattr(model, 'lines', []) or [])

    def payload(self) -> list[dict]:
        model = self.model
        return model.get_lines_data() if model is not None and hasattr(model, 'get_lines_data') else []

    def has_unit_support(self) -> bool:
        model = self.model
        return bool(model is not None and hasattr(model, 'COL_UNIT') and hasattr(model, 'get_lines_data'))


class InvoicePricingEngine:
    """Pricing boundary for invoice subtotal/discount/tax/final total."""

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


class InvoicePaymentsComponent:
    """Payment boundary for invoice document tabs."""

    def __init__(self, host) -> None:
        self.host = host

    def paid_amount(self) -> Decimal:
        try:
            return Decimal(str(self.host.paid_spin.value()))
        except Exception:
            return Decimal('0')


class InvoiceActionsComponent:
    """Command boundary wired to UnifiedActionBar and shortcuts."""

    def __init__(self, host) -> None:
        self.host = host

    def save(self) -> None:
        self.host.on_save()

    def print(self) -> None:
        self.host.print_invoice_professional()

    def export(self) -> None:
        self.print()
