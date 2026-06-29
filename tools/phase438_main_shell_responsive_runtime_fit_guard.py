#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard for Phase 438 main shell responsive runtime fit."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.main_shell_responsive_runtime_fit_contract import (  # noqa: E402
    main_shell_responsive_runtime_fit_matrix,
    main_shell_responsive_runtime_fit_summary,
)


def main() -> int:
    rows = main_shell_responsive_runtime_fit_matrix(ROOT)
    summary = main_shell_responsive_runtime_fit_summary(ROOT)
    out_dir = ROOT / "tools" / "audit_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "main_shell_responsive_runtime_fit_matrix.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["area", "check", "status"])
        writer.writeheader()
        writer.writerows(rows)
    (out_dir / "main_shell_responsive_runtime_fit_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    issues = [row for row in rows if row.get("status") != "pass"]
    if issues:
        print(json.dumps({"summary": summary, "issues": issues[:20]}, ensure_ascii=False, indent=2))
        return 1
    print(f"Phase 438 main shell responsive runtime fit guard passed: {summary['checks']} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
