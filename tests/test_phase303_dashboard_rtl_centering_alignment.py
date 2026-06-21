# -*- coding: utf-8 -*-
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_dashboard_rtl_structure_and_centered_identity_rules_are_present():
    src = read('alrajhi_client/views/widgets/dashboard_widget.py')
    ast.parse(src)
    assert 'row.setDirection(QBoxLayout.RightToLeft)' in src
    assert 'body.setDirection(QBoxLayout.RightToLeft)' in src
    assert '# Phase 303: identity banner is centered; surrounding structure remains RTL.' in src
    assert "title.setAlignment(Qt.AlignCenter)" in src
    assert "subtitle.setAlignment(Qt.AlignCenter)" in src
    assert "self.company_logo_label.setAlignment(Qt.AlignCenter)" in src
    assert "self.company_name_label.setAlignment(Qt.AlignCenter)" in src


def test_dashboard_shortcuts_centered_but_financial_inputs_right_aligned():
    src = read('alrajhi_client/views/widgets/dashboard_widget.py')
    legacy = read('alrajhi_client/views/widgets/dashboard_legacy_components.py')
    assert 'grid.addWidget(btn, i // 3, 2 - (i % 3))' in src
    assert "QPushButton { text-align: center; }" in src
    assert 'text-align: center' in legacy
    assert "self.exchange_rate_input.setAlignment(Qt.AlignRight | Qt.AlignVCenter)" in src
    assert "self.exchange_rate_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)" in src
    assert "balance_value.setAlignment(Qt.AlignCenter)" in src


def test_dashboard_alignment_phase_registered_in_release_gate():
    gate = read('alrajhi_client/workspace/quality/release_gate_contract.py')
    assert '(303, "DASHBOARD_RTL_CENTERING_ALIGNMENT")' in gate
    assert 'tests/test_phase303_dashboard_rtl_centering_alignment.py' in gate
    assert 'dashboard_rtl_centering_alignment' in gate
    assert (ROOT / 'PHASE303_DASHBOARD_RTL_CENTERING_ALIGNMENT.md').exists()
