# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtWidgets import QHeaderView

from features.transactions.grids.transaction_line_grid import TransactionLineGrid
from .restaurant_order_schema import restaurant_order_schema


class RestaurantOrderGrid(TransactionLineGrid):
    """Touch-friendly restaurant order grid using the shared grid engine."""

    def __init__(self, parent=None, identity: str = 'restaurant.order.lines'):
        super().__init__(restaurant_order_schema(), parent=parent, identity=identity)
        try:
            self.set_column_contract("restaurant", "order_lines")
        except Exception:
            pass
        try:
            self.setAlternatingRowColors(True)
            self.setSortingEnabled(False)
            self.setSelectionBehavior(self.SelectRows)
            self.setSelectionMode(self.SingleSelection)
            self.horizontalHeader().setSectionsMovable(True)
            self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        except Exception:
            pass
        self.apply_density('touch')

    def apply_density(self, density: str) -> None:
        density = str(density or 'touch').lower()
        row_h = 34 if density == 'compact' else 44 if density == 'comfortable' else 60
        try:
            self.verticalHeader().setDefaultSectionSize(row_h)
            self.verticalHeader().setMinimumSectionSize(max(26, row_h - 10))
        except Exception:
            pass

    def selected_row(self) -> int:
        try:
            idx = self.currentIndex()
            return idx.row() if idx.isValid() else -1
        except Exception:
            return -1

    def selected_line(self):
        try:
            model = self.model()
            row = self.selected_row()
            if row >= 0 and hasattr(model, 'line_at'):
                return model.line_at(row)
        except Exception:
            pass
        return None
