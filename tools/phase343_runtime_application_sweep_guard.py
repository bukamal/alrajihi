#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 343 guard: runtime application sweep for table contracts."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_FILE = OUT_DIR / "runtime_table_contract_sweep_matrix.csv"
SUMMARY_FILE = OUT_DIR / "runtime_table_contract_sweep_summary.json"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.runtime.table_contract_sweep import (  # noqa: E402
    contract_runtime_sweep_rows,
    validate_runtime_table_contract_sweep,
)


def _static_contains(path: str, needle: str) -> bool:
    return needle in (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [row.as_dict() for row in contract_runtime_sweep_rows()]
    issues = validate_runtime_table_contract_sweep()
    static_checks = {
        "custom_table_identity_autobind": ("alrajhi_client/views/custom_table_view.py", "table_column_contract_for_identity"),
        "cashboxes_contract_identities": ("alrajhi_client/views/widgets/cashboxes_widget.py", "cashboxes.cashboxes"),
        "branches_contract_identity": ("alrajhi_client/views/widgets/branches_widget.py", "branches.list"),
        "reports_contract_identity": ("alrajhi_client/views/widgets/reports_widget.py", "reports.result"),
    }
    for key, (path, needle) in static_checks.items():
        ok = _static_contains(path, needle)
        rows.append({"category": "static_wiring", "key": key, "contract_id": path, "ok": ok, "detail": needle})
        if not ok:
            issues.setdefault("static_wiring", []).append(key)
    with MATRIX_FILE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["category", "key", "contract_id", "ok", "detail"])
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "checks": len(rows),
        "issue_groups": len(issues),
        "issues_detail": issues,
        "matrix": str(MATRIX_FILE),
    }
    SUMMARY_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"runtime table sweep checks: {payload['checks']}")
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
