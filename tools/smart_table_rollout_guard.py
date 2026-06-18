#!/usr/bin/env python3
"""Guard for Phase 42 SmartTableView rollout.

The goal is not to forbid every QTableWidget in the ERP, because editable POS,
returns, and kitchen/order grids intentionally remain item-based. The guard
ensures management/list/report widgets no longer instantiate the legacy
CustomTableView directly and that the shared SmartTableView keeps the expected
capabilities.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WIDGETS = ROOT / "alrajhi_client" / "views" / "widgets"
SMART = ROOT / "alrajhi_client" / "ui" / "smart_table_view.py"

EXEMPT = {
    "modern_ui.py",
}


def main() -> int:
    failures: list[str] = []
    smart_source = SMART.read_text(encoding="utf-8")
    try:
        ast.parse(smart_source)
    except SyntaxError as exc:
        failures.append(f"SmartTableView parse error: {exc}")
    for token in ["class SmartTableView", "set_local_filter", "selected_source_rows", "export_to_excel", "print_table", "reset_layout"]:
        if token not in smart_source:
            failures.append(f"SmartTableView missing expected capability: {token}")

    for path in sorted(WIDGETS.glob("*.py")):
        if path.name in EXEMPT:
            continue
        source = path.read_text(encoding="utf-8")
        try:
            ast.parse(source)
        except SyntaxError as exc:
            failures.append(f"{path.relative_to(ROOT)} parse error: {exc}")
            continue
        if "from views.custom_table_view import CustomTableView" in source:
            failures.append(f"{path.relative_to(ROOT)} imports legacy CustomTableView")
        if "CustomTableView(" in source:
            failures.append(f"{path.relative_to(ROOT)} instantiates legacy CustomTableView")

    if failures:
        print("SmartTable rollout guard failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("SmartTable rollout guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
