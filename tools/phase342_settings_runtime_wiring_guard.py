#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 342 guard: settings surface runtime wiring and column customizer."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_FILE = OUT_DIR / "settings_runtime_wiring_matrix.csv"
SUMMARY_FILE = OUT_DIR / "settings_runtime_wiring_summary.json"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.settings.column_preferences import contract_column_states, validate_column_preference_runtime  # noqa: E402
from workspace.tables.table_column_registry import TABLE_COLUMN_CONTRACTS  # noqa: E402


def _static_check(path: str, needle: str) -> bool:
    return needle in (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    issues: dict[str, list[str]] = {}
    runtime_issues = validate_column_preference_runtime()
    for group, items in runtime_issues.items():
        issues[f"runtime_{group}"] = list(items)

    for contract_id in sorted(TABLE_COLUMN_CONTRACTS):
        states = contract_column_states(contract_id)
        rows.append({
            "check": "contract_runtime_state",
            "id": contract_id,
            "columns": len(states),
            "display_keys": ";".join(state.column_key for state in states if state.display),
            "print_keys": ";".join(state.column_key for state in states if state.print),
            "export_keys": ";".join(state.column_key for state in states if state.export),
        })
        if not states:
            issues.setdefault("empty_contract_state", []).append(contract_id)

    static_expectations = {
        "settings_widget_runtime_table": ("alrajhi_client/views/widgets/settings_widget.py", "settings_surface_columns_table"),
        "settings_widget_save_columns": ("alrajhi_client/views/widgets/settings_widget.py", "save_settings_surface_column_contract"),
        "runtime_dialog": ("alrajhi_client/views/dialogs/column_contract_customizer.py", "ColumnContractCustomizerDialog"),
        "custom_table_contract_dialog": ("alrajhi_client/views/custom_table_view.py", "show_contract_column_customizer"),
        "smart_table_contract_dialog": ("alrajhi_client/ui/smart_table_view.py", "show_contract_column_customizer"),
    }
    for check_id, (path, needle) in static_expectations.items():
        ok = _static_check(path, needle)
        rows.append({"check": check_id, "id": path, "columns": int(ok), "display_keys": needle, "print_keys": "", "export_keys": ""})
        if not ok:
            issues.setdefault("static_wiring", []).append(check_id)

    fields = ["check", "id", "columns", "display_keys", "print_keys", "export_keys"]
    with MATRIX_FILE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "checks": len(rows),
        "issue_groups": len(issues),
        "issues_detail": issues,
        "matrix": str(MATRIX_FILE),
    }
    SUMMARY_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"settings runtime wiring checks: {payload['checks']}")
    print(f"issue groups: {payload['issue_groups']}")
    print(f"matrix: {MATRIX_FILE}")
    print(f"summary: {SUMMARY_FILE}")
    if issues:
        for group, items in issues.items():
            for item in items:
                print(f"- {group}: {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
