#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 43 guard: preserve unified printing while adding workspace actions."""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def fail(msg: str) -> None:
    print(f"Unified printing guard failed:\n - {msg}")
    sys.exit(1)


def main() -> None:
    main_window = read("alrajhi_client/views/main_window.py")
    action_bar = read("alrajhi_client/shell/unified_action_bar.py")
    smart_table = read("alrajhi_client/ui/smart_table_view.py")
    custom_table = read("alrajhi_client/views/custom_table_view.py")

    for name, source in [
        ("main_window.py", main_window),
        ("unified_action_bar.py", action_bar),
        ("smart_table_view.py", smart_table),
        ("custom_table_view.py", custom_table),
    ]:
        try:
            ast.parse(source)
        except SyntaxError as exc:
            fail(f"{name}: syntax error: {exc}")

    if "UnifiedActionBar" not in main_window or "setup_action_bar" not in main_window:
        fail("MainWindow is not wired to UnifiedActionBar")
    if "self.action_bar.bind('print', self.print_current_tab)" not in main_window:
        fail("Action bar print must delegate to MainWindow.print_current_tab")
    if "QPrintDialog" in action_bar or "QPrinter" in action_bar or "QTextDocument" in action_bar:
        fail("UnifiedActionBar must not implement its own printing path")
    if "printing.printing_service" not in custom_table:
        fail("Table printing no longer uses the centralized printing service")
    if "print_table" not in smart_table:
        fail("SmartTableView context menu no longer exposes unified table printing")
    if "LegacySqlRepository" in action_bar:
        fail("UI action bar must not touch repositories or SQL bridges")
    print("Unified printing guard passed.")


if __name__ == "__main__":
    main()
