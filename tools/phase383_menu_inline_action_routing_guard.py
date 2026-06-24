#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'
OUT = ROOT / 'tools' / 'audit_outputs' / 'menu_inline_action_routing_matrix.csv'
SUMMARY = ROOT / 'tools' / 'audit_outputs' / 'menu_inline_action_routing_summary.json'
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.menu_inline_action_contract import menu_inline_action_matrix, menu_inline_action_summary  # noqa: E402


def main() -> int:
    rows = menu_inline_action_matrix(ROOT)
    summary = menu_inline_action_summary(ROOT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8-sig', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=['key', 'category', 'target', 'status', 'detail', 'phase'], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    payload = dict(summary)
    payload['matrix'] = str(OUT.relative_to(ROOT))
    SUMMARY.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    if summary['issues']:
        print(f"Phase383 menu inline action routing FAILED: {summary['issues']} issues")
        for row in rows:
            if row.get('status') != 'pass':
                print(f" - [{row.get('target')}::{row.get('category')}] {row.get('key')}: {row.get('detail')}")
        return 1
    print(f"Phase383 menu inline action routing passed: {summary['checks']} checks / 0 issues")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
