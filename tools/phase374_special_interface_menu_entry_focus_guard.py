# -*- coding: utf-8 -*-
"""Phase 374 guard for specialized interface menu and material-column focus."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))

from workspace.quality.special_interface_menu_entry_focus_contract import (  # noqa: E402
    special_interface_menu_entry_focus_matrix,
    special_interface_menu_entry_focus_summary,
)


def main() -> int:
    rows = special_interface_menu_entry_focus_matrix(ROOT)
    out = ROOT / "tools" / "audit_outputs" / "special_interface_menu_entry_focus_matrix.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=("key", "category", "description", "status", "detail"))
        writer.writeheader()
        writer.writerows(rows)
    summary = special_interface_menu_entry_focus_summary(ROOT)
    print(f"Phase 374 specialized menu/material focus guard: {summary['checks']} checks, {summary['issues']} issues")
    if summary["issues"]:
        for row in rows:
            if row.get("status") != "pass":
                print(f"FAIL {row['key']}: {row['description']} :: {row.get('detail','')}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
