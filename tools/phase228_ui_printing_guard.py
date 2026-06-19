# -*- coding: utf-8 -*-
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subprocess.check_call([sys.executable, str(ROOT / 'tools' / 'phase228_ui_printing_audit.py')], cwd=str(ROOT))
result = json.loads((ROOT / 'tools' / 'audit_outputs' / 'phase228_ui_printing_audit.json').read_text(encoding='utf-8'))
high = result.get('summary', {}).get('high', 0)
if high:
    raise AssertionError(f'Phase 228 UI/printing high findings remain: {high}')
print('phase228 ui/printing guard passed')
