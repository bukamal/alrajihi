#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard for Phase 371: reused Windows workflow with Warehouse-only output."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_PATH = OUT_DIR / "reused_windows_workflow_matrix.csv"
SUMMARY_PATH = OUT_DIR / "reused_windows_workflow_summary.json"

if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.reused_windows_workflow_contract import (  # noqa: E402
    reused_windows_workflow_matrix,
    reused_windows_workflow_summary,
)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = reused_windows_workflow_matrix(ROOT)
    summary = reused_windows_workflow_summary(ROOT)
    with MATRIX_PATH.open("w", encoding="utf-8-sig", newline="") as fh:
        fieldnames = ["key", "category", "description", "status", "detail", "phase"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    payload = dict(summary)
    payload["matrix"] = str(MATRIX_PATH.relative_to(ROOT))
    SUMMARY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if summary.get("issues"):
        print(f"Phase371 reused Windows workflow guard FAILED: {summary['issues']} issues")
        for row in rows:
            if row.get("status") != "pass":
                print(f" - [{row.get('category')}] {row.get('key')}: {row.get('detail')}")
        return 1
    print(f"Phase371 reused Windows workflow guard OK: {summary['checks']} checks / 0 issues")
    print(f"matrix: {MATRIX_PATH.relative_to(ROOT)}")
    print(f"summary: {SUMMARY_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
