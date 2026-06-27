#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))

from workspace.quality.language_runtime_switch_contract import (  # noqa: E402
    language_runtime_switch_matrix,
    language_runtime_switch_summary,
)

OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_PATH = OUT_DIR / "language_runtime_switch_matrix.csv"
SUMMARY_PATH = OUT_DIR / "language_runtime_switch_summary.json"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = language_runtime_switch_matrix(ROOT)
    summary = language_runtime_switch_summary(ROOT)
    if rows:
        with MATRIX_PATH.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if not summary["passed"]:
        print("Phase393 language runtime switch guard failed")
        for row in summary["failed_checks"]:
            print(f" - {row['check']}: {row['detail']}")
        return 1
    print(f"Phase393 language runtime switch guard passed: {summary['checks']} checks / 0 issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
