# -*- coding: utf-8 -*-
"""Phase 355 branded tables and transaction-footer tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'alrajhi_client'))


def test_table_identity_tokens_cover_light_and_dark():
    from theme.brand import BRAND, get_tokens
    from theme.table_identity import (
        REQUIRED_TABLE_TOKEN_KEYS,
        TABLE_IDENTITY_PHASE,
        validate_table_identity_tokens,
    )

    assert int(BRAND.get('brand_phase', 0)) >= TABLE_IDENTITY_PHASE
    assert 'table_current_bg' in REQUIRED_TABLE_TOKEN_KEYS
    assert 'transaction_footer_primary_bg' in REQUIRED_TABLE_TOKEN_KEYS
    assert validate_table_identity_tokens(get_tokens('light')) == {}
    assert validate_table_identity_tokens(get_tokens('dark')) == {}


def test_runtime_table_and_footer_wiring_markers_are_present():
    files = {
        'alrajhi_client/views/custom_table_view.py': [
            'brand_table_surface',
            'brand_table_density',
        ],
        'alrajhi_client/ui/table_keyboard_policy.py': [
            'brand_entry_table',
            'current_cell_highlight',
        ],
        'alrajhi_client/features/transactions/transaction_document_tab.py': [
            'TransactionFooterPanel',
            'TransactionFooterNotes',
            'transaction_footer_role',
        ],
        'alrajhi_client/features/transactions/components/transaction_totals_panel.py': [
            'TransactionHorizontalSummaryFrame',
            'TransactionHorizontalPaymentFrame',
            'TransactionSummaryValue',
            'transaction_footer_role',
        ],
        'alrajhi_client/features/transactions/components/transaction_bottom_actions.py': [
            'TransactionBottomActionBar',
            'transaction_action',
            'transaction_footer_role',
            'setMinimumWidth(126)',
        ],
        'alrajhi_client/theme/qss.py': [
            'Phase355: branded table surface and active editable cell',
            'Phase355: branded transaction footer and bottom commands',
            'brand_table_surface',
            'brand_entry_table',
            'transaction_footer_primary_bg',
        ],
    }
    for rel, markers in files.items():
        text = (ROOT / rel).read_text(encoding='utf-8')
        for marker in markers:
            assert marker in text


def test_phase355_guard_summary_is_clean():
    from workspace.quality.branded_tables_transaction_footer_contract import branded_tables_transaction_footer_summary

    summary = branded_tables_transaction_footer_summary(ROOT)
    assert summary['ready'] is True
    assert summary['issues'] == 0
    assert summary['checks'] >= 45
