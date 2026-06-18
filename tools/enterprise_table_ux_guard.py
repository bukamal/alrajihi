#!/usr/bin/env python3
"""Phase 60 guard for enterprise table UX.

Ensures the shared SmartTableView provides the capabilities requested for a
professional ERP grid and that critical list/report screens use stable table
identities so user column order/visibility survives restarts.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMART = ROOT / "alrajhi_client" / "ui" / "smart_table_view.py"
TOOLBAR = ROOT / "alrajhi_client" / "views" / "widgets" / "components" / "table_toolbar.py"
CRITICAL = [
    ROOT / "alrajhi_client" / "views" / "widgets" / "invoices_widget.py",
    ROOT / "alrajhi_client" / "views" / "widgets" / "reports_widget.py",
    ROOT / "alrajhi_client" / "views" / "widgets" / "warehouses_widget.py",
    ROOT / "alrajhi_client" / "views" / "widgets" / "vouchers_widget.py",
    ROOT / "alrajhi_client" / "views" / "widgets" / "manufacturing_widget.py",
]


def parse(path: Path, failures: list[str]) -> str:
    text = path.read_text(encoding="utf-8")
    try:
        ast.parse(text)
    except SyntaxError as exc:
        failures.append(f"{path.relative_to(ROOT)} parse error: {exc}")
    return text


def main() -> int:
    failures: list[str] = []
    smart = parse(SMART, failures)
    toolbar = parse(TOOLBAR, failures)

    for token in [
        "class ColumnChooserDialog",
        "show_column_chooser",
        "set_column_visible",
        "fit_columns_to_view",
        "export_to_pdf",
        "set_responsive_columns",
        "set_layout_profile",
        "setSectionsMovable(True)",
        "save_layout",
        "restore_layout",
    ]:
        if token not in smart:
            failures.append(f"SmartTableView missing enterprise table UX capability: {token}")

    for token in ["fitColumnsRequested", "show_column_chooser", "responsive_columns", "export_to_pdf"]:
        if token not in toolbar:
            failures.append(f"TableToolbar missing enterprise table UX wiring: {token}")

    for path in CRITICAL:
        text = parse(path, failures)
        if "SmartTableView" not in text:
            failures.append(f"{path.relative_to(ROOT)} does not use SmartTableView")
        if path.name in {"reports_widget.py", "warehouses_widget.py"} and "set_table_identity" not in text and "identity=" not in text:
            failures.append(f"{path.relative_to(ROOT)} lacks stable table identities")

    if failures:
        print("Enterprise table UX guard failed:")
        for f in failures:
            print(f" - {f}")
        return 1
    print("Enterprise table UX guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
