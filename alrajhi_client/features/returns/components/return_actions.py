# -*- coding: utf-8 -*-
from __future__ import annotations


class ReturnActionsComponent:
    """Command boundary consumed by the workspace action bar."""

    def __init__(self, host) -> None:
        self.host = host

    def save(self) -> None:
        self.host.accept()

    def print(self) -> None:
        self.host.workspace_print()

    def export(self) -> None:
        # Phase 235: no separate PDF export button/path from return documents.
        self.print()
