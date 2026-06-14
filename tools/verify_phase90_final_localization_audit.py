# -*- coding: utf-8 -*-
"""Verify Phase 90 final localization audit artifacts and critical invariants."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'GATEWAY_PHASE_90_LOCALIZATION_AUDIT' / 'translation_key_audit.json'


def main() -> None:
    if not REPORT.exists():
        raise SystemExit(f'missing audit report: {REPORT}')
    data = json.loads(REPORT.read_text(encoding='utf-8'))
    if data.get('ftranslate_refs'):
        raise SystemExit('ftranslate references remain')
    if data.get('parse_errors'):
        raise SystemExit('python parse errors found in localization audit')
    if data.get('missing_used_keys'):
        raise SystemExit('used translation keys missing from dictionaries: ' + ', '.join(data['missing_used_keys'][:20]))
    langs = set(data.get('languages', []))
    if langs != {'ar', 'de', 'en'}:
        raise SystemExit(f'unexpected languages: {langs}')
    print('phase90 final localization audit verified')


if __name__ == '__main__':
    main()
