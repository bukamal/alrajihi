#!/usr/bin/env python3
"""Guard against direct numeric comparisons on raw API/DB values in manufacturing UI."""
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / 'alrajhi_client' / 'views' / 'dialogs' / 'production_details_dialog.py',
    ROOT / 'alrajhi_client' / 'views' / 'dialogs' / 'production_order_dialog.py',
]
# Raw dict get compared directly to a number, e.g. it.get('average_cost', 0) > 0
bad_patterns = [
    re.compile(r"\.get\([^\n\)]*\)\s*[<>]=?\s*[-]?[0-9]"),
]
errors = []
for path in TARGETS:
    if not path.exists():
        continue
    text = path.read_text(encoding='utf-8')
    for i, line in enumerate(text.splitlines(), 1):
        if '_num(' in line:
            continue
        for pat in bad_patterns:
            if pat.search(line):
                errors.append(f"{path.relative_to(ROOT)}:{i}: direct numeric comparison on raw .get(): {line.strip()}")
if errors:
    print('\n'.join(errors))
    raise SystemExit(1)
print('manufacturing_numeric_guard: OK')
