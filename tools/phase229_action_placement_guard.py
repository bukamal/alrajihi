# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.check_call([sys.executable, str(ROOT / 'tools' / 'phase229_action_placement_audit.py')], cwd=str(ROOT))
result = json.loads((ROOT / 'tools' / 'audit_outputs' / 'phase229_action_placement_audit.json').read_text(encoding='utf-8'))
summary = result.get('summary', {})
if summary.get('high', 0):
    raise AssertionError(f"Phase 229 action placement high findings remain: {summary.get('high')}")
if summary.get('medium', 0):
    raise AssertionError(f"Phase 229 action placement medium findings remain: {summary.get('medium')}")
print('phase229 action placement guard passed')
