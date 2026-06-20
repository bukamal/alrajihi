#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the project-wide release readiness matrix (Phase 277)."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_FILE = OUT_DIR / "release_readiness_gate_matrix.csv"
SUMMARY_FILE = OUT_DIR / "release_readiness_gate_summary.json"

if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.release_gate_contract import (  # noqa: E402
    release_gate_matrix,
    release_gate_summary,
    validate_release_gate,
)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = release_gate_matrix(ROOT)
    fieldnames = [
        "key",
        "category",
        "title",
        "phase",
        "tool_path",
        "tool_exists",
        "output_path",
        "output_exists",
        "required",
    ]
    with MATRIX_FILE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    summary = release_gate_summary(ROOT)
    issues = validate_release_gate(ROOT)
    payload = dict(summary)
    payload["issues_detail"] = issues
    SUMMARY_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"release checks: {summary['checks']}")
    print(f"issue groups: {summary['issue_groups']}")
    print(f"matrix: {MATRIX_FILE}")
    print(f"summary: {SUMMARY_FILE}")
    if issues:
        print("Release readiness issues:")
        for group, items in issues.items():
            for item in items:
                print(f"- {group}: {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
