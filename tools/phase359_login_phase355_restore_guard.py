#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard for Phase 359: LoginDialog restored to Phase 355 design."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_PATH = OUT_DIR / "login_phase355_restore_matrix.csv"
SUMMARY_PATH = OUT_DIR / "login_phase355_restore_summary.json"

if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.login_phase355_restore_contract import (  # noqa: E402
    login_phase355_restore_matrix,
    login_phase355_restore_summary,
)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = login_phase355_restore_matrix(ROOT)
    summary = login_phase355_restore_summary(ROOT)
    with MATRIX_PATH.open("w", encoding="utf-8-sig", newline="") as fh:
        fieldnames = ["key", "category", "description", "status", "detail", "phase"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    payload = dict(summary)
    payload["matrix"] = str(MATRIX_PATH)
    SUMMARY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if summary.get("issues"):
        print(f"Phase359 login restore guard FAILED: {summary['issues']} issues")
        for row in rows:
            if row.get("status") != "pass":
                print(f" - [{row.get('category')}] {row.get('key')}: {row.get('detail')}")
        return 1
    print(f"Phase359 login restore guard OK: {summary['checks']} checks / 0 issues")
    print(f"matrix: {MATRIX_PATH}")
    print(f"summary: {SUMMARY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
