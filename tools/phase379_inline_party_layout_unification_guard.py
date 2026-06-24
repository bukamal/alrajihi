# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.inline_party_layout_unification_contract import inline_party_layout_unification_matrix, inline_party_layout_unification_summary  # noqa: E402

OUT = ROOT / 'tools' / 'audit_outputs' / 'inline_party_layout_unification_matrix.csv'


def main() -> int:
    rows = inline_party_layout_unification_matrix(ROOT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=['phase', 'category', 'target', 'key', 'status', 'detail'])
        writer.writeheader()
        writer.writerows(rows)
    summary = inline_party_layout_unification_summary(ROOT)
    if not summary['ready']:
        for row in rows:
            if row.get('status') != 'pass':
                print('FAIL:', row)
        return 1
    print(f"Phase379 inline party layout unification guard passed: {summary['checks']} checks / 0 issues")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
