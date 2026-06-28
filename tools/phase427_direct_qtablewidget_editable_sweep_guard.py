#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX = OUT_DIR / "direct_qtablewidget_editable_sweep_matrix.csv"


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def parses(rel: str) -> bool:
    try:
        ast.parse(read(rel))
        return True
    except SyntaxError:
        return False


def add(rows: list[dict[str, str]], key: str, category: str, path: str, ok: bool, detail: str) -> None:
    rows.append({"key": key, "category": category, "path": path, "status": "OK" if ok else "FAIL", "detail": detail})


def main() -> int:
    from workspace.quality.direct_qtablewidget_editable_sweep_contract import (
        PHASE427_DIRECT_QTABLEWIDGET_EDITABLE_SWEEP,
        direct_qtablewidget_surface_matrix,
        direct_qtablewidget_editable_sweep_summary,
    )

    rows: list[dict[str, str]] = []
    required = [
        "PHASE427_DIRECT_QTABLEWIDGET_EDITABLE_SWEEP.md",
        "alrajhi_client/workspace/quality/direct_qtablewidget_editable_sweep_contract.py",
        "tools/phase427_direct_qtablewidget_editable_sweep_guard.py",
        "tests/test_phase427_direct_qtablewidget_editable_sweep.py",
        "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py",
        "alrajhi_client/views/widgets/settings_widget.py",
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase427 file exists")
    for rel in required[1:]:
        add(rows, f"ast::{rel}", "syntax", rel, parses(rel), "source parses")

    add(rows, "contract_phase", "contract", required[1], PHASE427_DIRECT_QTABLEWIDGET_EDITABLE_SWEEP["phase"] == 427, "Phase427 contract declared")
    add(rows, "contract_owner", "contract", required[1], "EditableSmartGrid" in PHASE427_DIRECT_QTABLEWIDGET_EDITABLE_SWEEP["owner"], "EditableSmartGrid owns editable direct-table surfaces")

    summary = direct_qtablewidget_editable_sweep_summary(ROOT)
    add(rows, "summary_ready", "contract", required[1], bool(summary["ready"]), "all editable direct QTableWidget surfaces are migrated or classified read-only")

    restaurant = read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    settings = read("alrajhi_client/views/widgets/settings_widget.py")
    add(rows, "restaurant_invoice_grid_migrated", "source", required[4], "self.invoice_table = EditableSmartGrid" in restaurant, "restaurant simple POS invoice table uses EditableSmartGrid")
    add(rows, "restaurant_no_direct_qtablewidget", "source", required[4], "self.invoice_table = QTableWidget" not in restaurant, "restaurant simple POS invoice table no longer constructs QTableWidget")
    add(rows, "restaurant_no_selected_clicked", "source", required[4], "SelectedClicked" not in restaurant, "restaurant simple POS does not open editors through SelectedClicked")
    add(rows, "settings_surface_migrated", "source", required[5], "self.settings_surface_columns_table = EditableSmartGrid" in settings, "settings surface column table uses EditableSmartGrid")
    add(rows, "settings_surface_readonly", "source", required[5], "settings_surface_columns_table.setEditTriggers(EditableSmartGrid.NoEditTriggers)" in settings, "settings surface column table is explicitly non-editing")

    for row in direct_qtablewidget_surface_matrix(ROOT):
        rows.append({
            "key": f"direct::{row['path']}::{row['surface']}",
            "category": "direct_qtablewidget",
            "path": row["path"],
            "status": row["status"],
            "detail": f"line {row['line']}: {row['surface']} — {row['detail']}",
        })

    release = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    add(rows, "release_doc", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE427_DIRECT_QTABLEWIDGET_EDITABLE_SWEEP" in release, "Phase427 doc registered")
    add(rows, "release_test", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "tests/test_phase427_direct_qtablewidget_editable_sweep.py" in release, "Phase427 test registered")
    add(rows, "release_check", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "direct_qtablewidget_editable_sweep" in release and "phase=427" in release, "Phase427 release check registered")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with MATRIX.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader(); writer.writerows(rows)

    failed = [row for row in rows if row["status"] != "OK"]
    print(f"Phase427 direct QTableWidget editable sweep checks: {len(rows)} checks, failures={len(failed)}")
    print(f"Matrix: {MATRIX}")
    for row in failed:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
