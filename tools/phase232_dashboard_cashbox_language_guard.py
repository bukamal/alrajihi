# -*- coding: utf-8 -*-
"""Phase 232 guard: dashboard cashbox source and visible-language hygiene."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_WIDGET = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'dashboard_widget.py'
DASHBOARD_SERVICE = ROOT / 'alrajhi_client' / 'core' / 'services' / 'dashboard_service.py'
TRANSLATOR = ROOT / 'alrajhi_client' / 'i18n' / 'translator.py'
OUT_DIR = ROOT / 'tools' / 'audit_outputs'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def _assert(condition: bool, message: str, findings: list[dict], severity: str = 'high'):
    if not condition:
        findings.append({'severity': severity, 'message': message})


def _count_function(path: Path, name: str) -> int:
    tree = ast.parse(_read(path))
    return sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name)



def run() -> list[dict]:
    findings: list[dict] = []
    dashboard = _read(DASHBOARD_WIDGET)
    service = _read(DASHBOARD_SERVICE)
    translator = _read(TRANSLATOR)

    _assert("'cash_bank_summary'" in service, 'DashboardService.snapshot must include cash_bank_summary.', findings)
    _assert('reporting_service.cash_bank_summary()' in service, 'DashboardService.summary must prefer modern cash/bank liquidity summary.', findings)
    _assert('reporting_service.cash_bank_movements' in service, 'DashboardService.cashbox_movement must read the cash/bank movement ledger.', findings)
    _assert('_summarize_movements' in service, 'DashboardService must summarize real cash/bank movement rows.', findings)

    _assert("self._snapshot.get('cash_bank_summary'" in dashboard, 'DashboardWidget must read cash_bank_summary from the snapshot.', findings)
    _assert('currency.format_base_amount(amount)' in dashboard, 'Dashboard cashbox amounts must use currency.format_base_amount.', findings)
    _assert("currency.convert(amount, 'USD'" not in dashboard, 'Dashboard cashbox rendering must not hard-code USD conversions.', findings)
    _assert("f'1 USD =" not in dashboard, 'Dashboard exchange-rate label must not hard-code USD.', findings)
    _assert("self.queue_status.setText(f'Queue:" not in dashboard, 'Dashboard queue status must use translation keys.', findings)
    _assert(_count_function(DASHBOARD_WIDGET, '_render_cash_amounts') == 1, 'DashboardWidget must not contain duplicate _render_cash_amounts definitions.', findings)
    _assert(_count_function(DASHBOARD_WIDGET, '_toggle_cash_visibility') == 1, 'DashboardWidget must not contain duplicate _toggle_cash_visibility definitions.', findings)

    for key in ('api_status_placeholder', 'queue_status_placeholder', 'ledger_status_placeholder', 'queue_pending_short', 'exchange_rate_value'):
        _assert(key in translator, f'Missing translation key: {key}', findings)

    report = {
        'phase': 232,
        'title': 'Dashboard cashbox and language audit',
        'findings': findings,
        'summary': {
            'high': sum(1 for f in findings if f['severity'] == 'high'),
            'medium': sum(1 for f in findings if f['severity'] == 'medium'),
            'low': sum(1 for f in findings if f['severity'] == 'low'),
        },
    }
    (OUT_DIR / 'phase232_dashboard_cashbox_language_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT_DIR / 'PHASE232_DASHBOARD_CASHBOX_LANGUAGE_AUDIT.md').write_text(
        '# Phase 232 Dashboard Cashbox / Language Audit\n\n'
        f"Summary: `{report['summary']}`\n\n"
        + ('No blocking findings.\n' if not findings else '\n'.join(f"- {f['severity']}: {f['message']}" for f in findings)),
        encoding='utf-8',
    )
    return findings


if __name__ == '__main__':
    findings = run()
    if any(f['severity'] in {'high', 'medium'} for f in findings):
        for item in findings:
            print(f"{item['severity'].upper()}: {item['message']}")
        raise SystemExit(1)
    print('Phase 232 dashboard cashbox/language guard passed')
