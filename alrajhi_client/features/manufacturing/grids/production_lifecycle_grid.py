# -*- coding: utf-8 -*-
from __future__ import annotations

from features.transactions.grids.transaction_line_grid import TransactionLineGrid


class ProductionLifecycleGrid(TransactionLineGrid):
    """Read-only lifecycle grid for manufacturing reservations, consumptions and outputs."""

    def __init__(self, columns=None, parent=None, identity: str = 'manufacturing.production.lifecycle'):
        super().__init__(columns=columns, parent=parent, identity=identity)
