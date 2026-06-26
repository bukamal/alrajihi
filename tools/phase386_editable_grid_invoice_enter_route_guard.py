#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT = ROOT / "tools" / "audit_outputs" / "editable_grid_invoice_enter_route_matrix.csv"
SUMMARY = ROOT / "tools" / "audit_outputs" / "editable_grid_invoice_enter_route_summary.json"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.editable_grid_invoice_enter_route_contract import (  # noqa: E402
    editable_grid_invoice_enter_route_matrix,
    editable_grid_invoice_enter_route_summary,
)


def main() -> int:
    rows = editable_grid_invoice_enter_route_matrix(ROOT)
    summary = editable_grid_invoice_enter_route_summary(ROOT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "target", "status", "detail", "phase"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    payload = dict(summary)
    payload["matrix"] = str(OUT.relative_to(ROOT))
    SUMMARY.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if summary["issues"]:
        print(f"Phase386 editable-grid invoice Enter route FAILED: {summary['issues']} issues")
        for row in rows:
            if row.get("status") != "pass":
                print(f" - [{row.get('target')}] {row.get('key')}: {row.get('detail')}")
        return 1
    print(f"Phase386 editable-grid invoice Enter route passed: {summary['checks']} checks / 0 issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
