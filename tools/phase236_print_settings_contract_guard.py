# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    subprocess.check_call([sys.executable, str(ROOT / 'tools' / 'phase236_print_settings_contract_audit.py')], cwd=str(ROOT))
    data = json.loads((ROOT / 'tools' / 'audit_outputs' / 'phase236_print_settings_contract_audit.json').read_text(encoding='utf-8'))
    high = data.get('summary', {}).get('high', 0)
    medium = data.get('summary', {}).get('medium', 0)
    if high or medium:
        findings = data.get('findings', [])[:40]
        details = '\n'.join(f"{f['severity']}: {f['path']}:{f['line']} {f['message']}" for f in findings)
        raise AssertionError('Phase 236 print settings contract failed:\n' + details)
    print('Phase 236 print settings contract guard passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
