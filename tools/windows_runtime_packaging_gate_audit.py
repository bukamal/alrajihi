#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Windows runtime packaging gate outputs (Phase 278)."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_FILE = OUT_DIR / "windows_runtime_packaging_gate_matrix.csv"
SUMMARY_FILE = OUT_DIR / "windows_runtime_packaging_gate_summary.json"

if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.packaging.windows_packaging_gate_contract import (  # noqa: E402
    packaging_gate_matrix,
    validate_windows_packaging_gate,
    windows_packaging_gate_summary,
)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = packaging_gate_matrix(ROOT)
    fieldnames = ["key", "category", "title", "required", "status", "issues"]
    with MATRIX_FILE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    summary = windows_packaging_gate_summary(ROOT)
    issues = validate_windows_packaging_gate(ROOT)
    payload = dict(summary)
    payload["issues_detail"] = issues
    SUMMARY_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"windows packaging checks: {summary['checks']}")
    print(f"issue groups: {summary['issue_groups']}")
    print(f"matrix: {MATRIX_FILE}")
    print(f"summary: {SUMMARY_FILE}")
    if issues:
        print("Windows runtime packaging issues:")
        for group, items in issues.items():
            for item in items:
                print(f"- {group}: {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
