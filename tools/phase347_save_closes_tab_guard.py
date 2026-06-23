#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 347 guard: successful Save closes the owning workspace tab."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_FILE = OUT_DIR / "save_closes_tab_matrix.csv"
SUMMARY_FILE = OUT_DIR / "save_closes_tab_summary.json"

if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.shell.save_close_after_save_contract import (  # noqa: E402
    save_close_checks,
    save_close_issues,
    save_close_summary,
)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = save_close_checks(ROOT)
    with MATRIX_FILE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "title", "status", "detail"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_row())
    summary = dict(save_close_summary(ROOT))
    issues = save_close_issues(ROOT)
    summary["issues_detail"] = issues
    summary["matrix"] = str(MATRIX_FILE)
    SUMMARY_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"save-close checks: {summary['checks']}")
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
