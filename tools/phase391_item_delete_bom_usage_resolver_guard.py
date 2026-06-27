#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.item_delete_bom_usage_resolver_contract import (  # noqa: E402
    item_delete_bom_usage_resolver_matrix,
    item_delete_bom_usage_resolver_summary,
)

OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX_PATH = OUT_DIR / "item_delete_bom_usage_resolver_matrix.csv"
SUMMARY_PATH = OUT_DIR / "item_delete_bom_usage_resolver_summary.json"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = item_delete_bom_usage_resolver_matrix(ROOT)
    summary = item_delete_bom_usage_resolver_summary(ROOT)
    with MATRIX_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "description", "path", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if not summary["ready"]:
        print(f"Phase391 guard failed: {summary['failed_keys']}")
        return 1
    print(f"Phase391 item delete BOM usage resolver: OK ({summary['checks']} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
