# -*- coding: utf-8 -*-
from __future__ import annotations

from features.transactions.grids.transaction_line_grid import TransactionLineGrid


class ProductionRequiredMaterialsGrid(TransactionLineGrid):
    """Read-only production requirements grid sharing professional table behaviour."""

    def __init__(self, columns=None, parent=None, identity: str = 'manufacturing.production.required_materials'):
        super().__init__(columns=columns, parent=parent, identity=identity)
