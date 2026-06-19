# -*- coding: utf-8 -*-
from __future__ import annotations


class InvoiceActionsComponent:
    """Command boundary wired to UnifiedActionBar and keyboard shortcuts."""

    def __init__(self, host) -> None:
        self.host = host

    def save(self) -> None:
        self.host.on_save()

    def print(self) -> None:
        self.host.print_invoice_professional()

    def export(self) -> None:
        # Phase 235: document export no longer exposes a separate PDF path; use the unified print contract.
        self.print()

    def refresh(self) -> None:
        if hasattr(self.host, 'workspace_refresh'):
            self.host.workspace_refresh()
