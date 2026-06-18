# -*- coding: utf-8 -*-
from __future__ import annotations

from features.transactions.grids.transaction_line_grid import TransactionLineGrid


class InventoryTransferGrid(TransactionLineGrid):
    """Warehouse transfer line grid using the shared item/unit delegates."""

    def __init__(self, columns=None, parent=None, identity: str | None = None):
        super().__init__(columns=columns, parent=parent, identity=identity or 'inventory.transfer.lines')
        self.apply_named_preset('manager')
