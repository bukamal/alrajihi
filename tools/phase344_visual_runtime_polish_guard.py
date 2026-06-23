#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 344 guard: visual runtime polish sweep."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_FILE = OUT_DIR / "visual_runtime_polish_matrix.csv"
SUMMARY_FILE = OUT_DIR / "visual_runtime_polish_summary.json"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.runtime.visual_polish_contract import (  # noqa: E402
    validate_visual_polish_contract,
    visual_polish_rows,
)


def _static_contains(path: str, needle: str) -> bool:
    return needle in (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [dict(row) for row in visual_polish_rows()]
    issues = validate_visual_polish_contract()
    static_checks = {
        "main_window_runtime_polish_hook": ("alrajhi_client/views/main_window.py", "apply_runtime_visual_polish"),
        "runtime_visual_polish_module": ("alrajhi_client/ui/runtime_visual_polish.py", "visualWorkspaceType"),
        "runtime_qss_selectors": ("alrajhi_client/theme/qss.py", "Phase 344: runtime visual polish sweep"),
        "table_visual_role": ("alrajhi_client/ui/runtime_visual_polish.py", "runtime_table"),
    }
    for key, (path, needle) in static_checks.items():
        ok = _static_contains(path, needle)
        rows.append({"category": "static_wiring", "key": key, "workspace_type": path, "ok": ok, "detail": needle})
        if not ok:
            issues.setdefault("static_wiring", []).append(key)
    with MATRIX_FILE.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["category", "key", "workspace_type", "ok", "detail"])
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "checks": len(rows),
        "issue_groups": len(issues),
        "issues_detail": issues,
        "matrix": str(MATRIX_FILE),
    }
    SUMMARY_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"visual runtime polish checks: {payload['checks']}")
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
