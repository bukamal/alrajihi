#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 341 guard: unified settings surface for UI columns and barcode profiles."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_FILE = OUT_DIR / "settings_surface_matrix.csv"
SUMMARY_FILE = OUT_DIR / "settings_surface_summary.json"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.settings.preferences_surface_contract import settings_surface_matrix, validate_settings_surface  # noqa: E402


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = settings_surface_matrix()
    fields = ["surface_type", "id", "title", "settings_prefix", "settings_count", "setting_keys"]
    with MATRIX_FILE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    issues = validate_settings_surface()
    payload = {
        "checks": len(rows),
        "issue_groups": len(issues),
        "issues_detail": issues,
        "matrix": str(MATRIX_FILE),
    }
    SUMMARY_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"settings surface checks: {payload['checks']}")
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
