#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'
OUT = ROOT / 'tools' / 'audit_outputs' / 'document_layout_family_contract_matrix.csv'
SUMMARY = ROOT / 'tools' / 'audit_outputs' / 'document_layout_family_contract_summary.json'
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.document_layout_family_contract import document_layout_family_matrix, document_layout_family_summary  # noqa: E402


def main() -> int:
    rows = document_layout_family_matrix(ROOT)
    summary = document_layout_family_summary(ROOT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8-sig', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=['key', 'category', 'target', 'status', 'detail', 'phase'], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    payload = dict(summary)
    payload['matrix'] = str(OUT.relative_to(ROOT))
    SUMMARY.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    if summary['issues']:
        print(f"Phase381 document layout family contract FAILED: {summary['issues']} issues")
        for row in rows:
            if row.get('status') != 'pass':
                print(f" - [{row.get('target')}::{row.get('category')}] {row.get('key')}: {row.get('detail')}")
        return 1
    print(f"Phase381 document layout family contract passed: {summary['checks']} checks / 0 issues")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
