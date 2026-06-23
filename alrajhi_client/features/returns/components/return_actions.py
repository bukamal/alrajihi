# -*- coding: utf-8 -*-
from __future__ import annotations


class ReturnActionsComponent:
    """Command boundary consumed by the workspace action bar."""

    def __init__(self, host) -> None:
        self.host = host

    def save(self) -> None:
        # Phase 346: embedded tab save buttons persist only; they must not close
        # the workspace tab.  Dialog-level accept remains available for true
        # modal usages through host.accept().
        if hasattr(self.host, '_save_return_document'):
            self.host._save_return_document(close_after_save=False)
        else:
            self.host.accept()

    def print(self) -> None:
        self.host.workspace_print()

    def export(self) -> None:
        # Phase 235: no separate PDF export button/path from return documents.
        self.print()
