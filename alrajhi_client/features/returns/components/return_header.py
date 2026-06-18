# -*- coding: utf-8 -*-
from __future__ import annotations


class ReturnHeaderComponent:
    """Header boundary for sales/purchase return document tabs."""

    def __init__(self, host) -> None:
        self.host = host

    def data(self) -> dict:
        invoice_id = self.host.invoice_combo.currentData() if hasattr(self.host, 'invoice_combo') else None
        inv = getattr(self.host, 'invoice_map', {}).get(invoice_id, {}) or {}
        return {
            'original_invoice_id': invoice_id,
            'invoice_reference': inv.get('reference') or inv.get('invoice_no') or inv.get('number') or '',
            'date': self.host.date_edit.date().toString('yyyy-MM-dd') if hasattr(self.host, 'date_edit') else '',
            'warehouse_id': self.host.warehouse_combo.currentData() if hasattr(self.host, 'warehouse_combo') else None,
            'notes': self.host.notes_edit.toPlainText().strip() if hasattr(self.host, 'notes_edit') else '',
        }
