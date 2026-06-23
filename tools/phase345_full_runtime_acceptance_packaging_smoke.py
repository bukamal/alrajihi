#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 345 guard: full runtime acceptance and packaging smoke."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_FILE = OUT_DIR / "full_runtime_acceptance_packaging_smoke_matrix.csv"
SUMMARY_FILE = OUT_DIR / "full_runtime_acceptance_packaging_smoke_summary.json"

if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.full_runtime_acceptance_contract import (  # noqa: E402
    runtime_acceptance_issues,
    runtime_acceptance_rows,
    runtime_acceptance_summary,
)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = runtime_acceptance_rows(ROOT, include_manual=True)
    fieldnames = ["key", "category", "title", "status", "required", "domain", "detail"]
    with MATRIX_FILE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_row())
    summary = dict(runtime_acceptance_summary(ROOT))
    issues = runtime_acceptance_issues(rows)
    summary["issues_detail"] = issues
    summary["matrix"] = str(MATRIX_FILE)
    SUMMARY_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"runtime acceptance smoke checks: {summary['checks']}")
    print(f"automated checks: {summary['automated_checks']}")
    print(f"manual checks: {summary['manual_checks']}")
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
