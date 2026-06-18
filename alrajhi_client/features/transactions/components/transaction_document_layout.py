# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QSizePolicy


class TransactionDocumentLayout:
    """Shared transaction workspace layout contract.

    It upgrades invoice-like screens from a dialog-shaped form to a document
    workspace: compact header, dominant line grid, responsive totals panel, and
    bottom action bar.  It does not perform data access and can be reused by
    sales, purchases, returns, POS and restaurant checkout.
    """

    def __init__(self, host, *, transaction_type: str = "sale") -> None:
        self.host = host
        self.transaction_type = transaction_type or "sale"

    def apply(self) -> None:
        self._apply_embedded_workspace_rules()
        self._configure_splitter()
        self._configure_grid()
        self._configure_actions()

    def _apply_embedded_workspace_rules(self) -> None:
        # In tabs the shell already shows a title.  Hiding the legacy title card
        # frees vertical space for the line grid, which is the main work area.
        if getattr(self.host, "_embedded_mode", False) and hasattr(self.host, "title_frame"):
            self.host.title_frame.setVisible(False)
        if hasattr(self.host, "content_widget"):
            self.host.content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _configure_splitter(self) -> None:
        splitter = getattr(self.host, "content_splitter", None)
        if splitter is None:
            return
        splitter.setObjectName("TransactionDocumentSplitter")
        splitter.setChildrenCollapsible(False)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 2)
        QTimer.singleShot(0, lambda: splitter.setSizes([980, 320]))

    def _configure_grid(self) -> None:
        grid = getattr(self.host, "lines_table", None)
        if grid is None:
            return
        grid.setObjectName("TransactionLineGrid")
        grid.setMinimumHeight(440)
        grid.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if hasattr(grid, "apply_transaction_profile"):
            QTimer.singleShot(0, grid.apply_transaction_profile)

    def _configure_actions(self) -> None:
        bottom_bar = getattr(self.host, "bottom_action_bar", None)
        if bottom_bar is not None:
            bottom_bar.setObjectName("TransactionBottomActionBar")
            bottom_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
