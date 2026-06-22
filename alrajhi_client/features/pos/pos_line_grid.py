# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtWidgets import QHeaderView

from features.transactions.grids.transaction_line_grid import TransactionLineGrid
from .pos_line_schema import pos_line_schema


class POSLineGrid(TransactionLineGrid):
    """Touch-friendly POS cart grid using the shared transaction grid engine."""

    def __init__(self, parent=None, identity: str = 'pos.lines'):
        super().__init__(pos_line_schema(), parent=parent, identity=identity)
        try:
            self.set_column_contract("pos", "lines")
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

    def apply_density(self, density: str) -> None:
        density = str(density or 'touch').lower()
        row_h = 32 if density == 'compact' else 42 if density == 'comfortable' else 58
        try:
            self.verticalHeader().setDefaultSectionSize(row_h)
            self.verticalHeader().setMinimumSectionSize(max(24, row_h - 10))
        except Exception:
            pass

    def selected_row(self) -> int:
        try:
            idx = self.currentIndex()
            return idx.row() if idx.isValid() else -1
        except Exception:
            return -1
