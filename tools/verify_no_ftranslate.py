#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
violations = []
for p in (ROOT / "alrajhi_client").rglob("*.py"):
    if "__pycache__" in p.parts:
        continue
    txt = p.read_text(encoding="utf-8", errors="ignore")
    for i, line in enumerate(txt.splitlines(), 1):
        if "ftranslate" in line:
            violations.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()}")
if violations:
    print("ERROR: undefined ftranslate references remain:")
    print("\n".join(violations))
    sys.exit(1)
print("OK: no ftranslate references")
