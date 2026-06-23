#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 346 guard: fixed dashboard and tab lifecycle fallback."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_FILE = OUT_DIR / "tab_lifecycle_dashboard_fallback_matrix.csv"
SUMMARY_FILE = OUT_DIR / "tab_lifecycle_dashboard_fallback_summary.json"

if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.shell.tab_lifecycle_contract import (  # noqa: E402
    tab_lifecycle_checks,
    tab_lifecycle_issues,
    tab_lifecycle_summary,
)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = tab_lifecycle_checks(ROOT)
    with MATRIX_FILE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "title", "status", "detail"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_row())
    summary = dict(tab_lifecycle_summary(ROOT))
    issues = tab_lifecycle_issues(ROOT)
    summary["issues_detail"] = issues
    summary["matrix"] = str(MATRIX_FILE)
    SUMMARY_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"tab lifecycle checks: {summary['checks']}")
    print(f"issue groups: {summary['issue_groups']}")
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
