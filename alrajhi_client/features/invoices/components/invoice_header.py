# -*- coding: utf-8 -*-
from __future__ import annotations


class InvoiceHeaderComponent:
    """Document-tab header boundary for invoice party/date/reference/warehouse state.

    The legacy invoice widget still owns the Qt controls during the transition,
    but all workspace/document code should read and write header state through
    this component instead of touching controls ad hoc.
    """

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

    def set_reference(self, reference: str) -> None:
        if hasattr(self.host, 'ref_edit'):
            self.host.ref_edit.setText(reference or '')
