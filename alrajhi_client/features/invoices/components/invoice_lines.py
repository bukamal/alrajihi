# -*- coding: utf-8 -*-
from __future__ import annotations


class InvoiceLinesComponent:
    """Unit-aware invoice lines boundary.

    This component keeps item/unit line operations reusable by sales invoices,
    purchase invoices, returns, restaurant checkout, and fast POS flows.
    """

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

    def add_empty_line(self) -> None:
        if hasattr(self.host, 'add_empty_line'):
            self.host.add_empty_line()

    def has_unit_support(self) -> bool:
        model = self.model
        if model is None:
            return False
        return all(hasattr(model, name) for name in ('COL_UNIT', 'get_lines_data'))
