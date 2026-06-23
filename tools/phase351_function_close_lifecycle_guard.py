#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "alrajhi_client") not in sys.path:
    sys.path.insert(0, str(ROOT / "alrajhi_client"))

from workspace.quality.function_close_unification_contract import phase351_checks, phase351_issues


def main() -> int:
    out_dir = ROOT / "tools" / "audit_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks = phase351_checks(ROOT)
    issues = phase351_issues(ROOT)
    matrix = out_dir / "function_close_lifecycle_matrix.csv"
    summary = out_dir / "function_close_lifecycle_summary.json"
    with matrix.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["code", "area", "title", "path", "ok", "detail"])
        writer.writeheader()
        for check in checks:
            writer.writerow({
                "code": check.code,
                "area": check.area,
                "title": check.title,
                "path": check.path,
                "ok": check.ok,
                "detail": check.detail,
            })
    summary.write_text(json.dumps({
        "phase": 351,
        "checks": len(checks),
        "issues": len(issues),
        "matrix": str(matrix),
        "issue_codes": [issue.code for issue in issues],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    if issues:
        for issue in issues:
            print(f"FAIL {issue.code}: {issue.title}")
        return 1
    print(f"Phase351 function close lifecycle guard passed: {len(checks)} checks / 0 issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
