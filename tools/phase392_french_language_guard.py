#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))

from workspace.quality.french_language_contract import french_language_matrix, french_language_summary  # noqa: E402

OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_PATH = OUT_DIR / "french_language_matrix.csv"
SUMMARY_PATH = OUT_DIR / "french_language_summary.json"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = french_language_matrix(ROOT)
    summary = french_language_summary(ROOT)
    if rows:
        with MATRIX_PATH.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if not summary["passed"]:
        print("Phase392 French language guard failed")
        for row in summary["failed_checks"]:
            print(f" - {row['check']}: {row['detail']}")
        return 1
    print(f"Phase392 French language guard passed: {summary['checks']} checks / 0 issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
