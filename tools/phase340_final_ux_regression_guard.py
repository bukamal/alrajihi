#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 340 final UX regression guard."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_FILE = OUT_DIR / "final_ux_regression_matrix.csv"
SUMMARY_FILE = OUT_DIR / "final_ux_regression_summary.json"

if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.final_ux_regression_contract import (  # noqa: E402
    final_ux_regression_checks,
    final_ux_regression_summary,
)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    checks = final_ux_regression_checks()
    fieldnames = ["key", "category", "title", "ok", "detail"]
    with MATRIX_FILE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for check in checks:
            writer.writerow(check.as_row())
    summary = final_ux_regression_summary()
    issues = [check.as_row() for check in checks if not check.ok]
    payload = dict(summary)
    payload["issues_detail"] = issues
    SUMMARY_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"final UX checks: {summary['checks']}")
    print(f"issues: {summary['issues']}")
    print(f"matrix: {MATRIX_FILE}")
    print(f"summary: {SUMMARY_FILE}")
    if issues:
        for issue in issues:
            print(f"- {issue['key']}: {issue['detail']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
