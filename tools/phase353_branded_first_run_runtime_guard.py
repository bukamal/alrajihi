#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 353 guard: branded login, splash and activation runtime wiring."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workspace.quality.branded_first_run_runtime_contract import (  # noqa: E402
    branded_first_run_runtime_matrix,
    branded_first_run_runtime_summary,
)

OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
MATRIX_PATH = OUT_DIR / "branded_first_run_runtime_matrix.csv"
SUMMARY_PATH = OUT_DIR / "branded_first_run_runtime_summary.json"


def main() -> int:
    rows = branded_first_run_runtime_matrix(ROOT)
    summary = branded_first_run_runtime_summary(ROOT)

    with MATRIX_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["key", "category", "description", "status", "detail"])
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in writer.fieldnames})

    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    if summary["issues"]:
        print(f"Phase353 branded first-run runtime guard FAILED: {summary['issues']} issues")
        for row in rows:
            if row.get("status") != "pass":
                print(f" - [{row.get('category')}] {row.get('key')}: {row.get('detail')}")
        return 1

    print(f"Phase353 branded first-run runtime guard passed: {summary['checks']} checks / 0 issues")
    print(f"matrix: {MATRIX_PATH.relative_to(ROOT)}")
    print(f"summary: {SUMMARY_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
