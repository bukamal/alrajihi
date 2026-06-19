#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 220 guard: party document shell is not a legacy form-only tab."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTY_TAB = ROOT / 'alrajhi_client' / 'features' / 'parties' / 'party_editor_tab.py'
TRANSLATOR = ROOT / 'alrajhi_client' / 'i18n' / 'translator.py'
DASHBOARD = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'dashboard_widget.py'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    src = PARTY_TAB.read_text(encoding='utf-8')
    tr = TRANSLATOR.read_text(encoding='utf-8')
    dash = DASHBOARD.read_text(encoding='utf-8') if DASHBOARD.exists() else ''

    required_tokens = [
        'DocumentHeaderCard',
        'SummaryPanel',
        'BottomActionBar',
        'party_identity_panel',
        'party_contact_panel',
        'party_balance_panel',
        'party_context_title',
        'MetricCard',
        'format_base_amount',
        'refresh_context_tables',
        'party_operation_policy.can',
    ]
    for token in required_tokens:
        require(token in src, f'PartyEditorTab missing document-shell token: {token}')

    forbidden_tokens = [
        'self.details_page = QWidget',
        "self.tabs.addTab(self.details_page",
        "currency.format_amount(total)",
        "currency.format_amount(amount)",
    ]
    for token in forbidden_tokens:
        require(token not in src, f'PartyEditorTab still contains legacy form/currency pattern: {token}')

    for key in [
        'party_identity_panel',
        'party_contact_panel',
        'party_balance_panel',
        'party_current_balance',
        'party_invoice_remaining',
        'party_voucher_total',
    ]:
        require(key in tr, f'Missing party shell translation key: {key}')

    require('AddEntityDialog(' not in dash, 'Dashboard must not open AddEntityDialog directly')
    require('open_party_document' in dash, 'Dashboard quick actions should route parties to document tabs')

    print('phase220 party document shell guard passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
