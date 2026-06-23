#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard for Phase 360: organized RTL login layout."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_PATH = OUT_DIR / "login_rtl_layout_matrix.csv"
SUMMARY_PATH = OUT_DIR / "login_rtl_layout_summary.json"

if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.login_rtl_layout_contract import (  # noqa: E402
    login_rtl_layout_matrix,
    login_rtl_layout_summary,
)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = login_rtl_layout_matrix(ROOT)
    summary = login_rtl_layout_summary(ROOT)
    with MATRIX_PATH.open("w", encoding="utf-8-sig", newline="") as fh:
        fieldnames = ["key", "category", "description", "status", "detail", "phase"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    payload = dict(summary)
    payload["matrix"] = str(MATRIX_PATH.relative_to(ROOT))
    SUMMARY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if summary.get("issues"):
        print(f"Phase360 login RTL layout guard FAILED: {summary['issues']} issues")
        for row in rows:
            if row.get("status") != "pass":
                print(f" - [{row.get('category')}] {row.get('key')}: {row.get('detail')}")
        return 1
    print(f"Phase360 login RTL layout guard OK: {summary['checks']} checks / 0 issues")
    print(f"matrix: {MATRIX_PATH.relative_to(ROOT)}")
    print(f"summary: {SUMMARY_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
