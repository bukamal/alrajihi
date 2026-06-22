from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_phase328_dashboard_cards_expand_and_shortcuts_centered():
    src = read('alrajhi_client/views/widgets/dashboard_widget.py')
    legacy = read('alrajhi_client/views/widgets/dashboard_legacy_components.py')
    assert 'Phase 328: dashboard cards fill the landing page' in src
    assert 'panel.setMinimumHeight(500)' in src
    assert 'self.main_layout.addLayout(row, 1)' in src
    assert 'btn.setMinimumHeight(92)' in src
    assert 'btn.setIconSize(QSize(24, 24))' in src
    assert "super().__init__(qta.icon(f'fa5s.{icon_name}', color='white'), str(text), parent)" in legacy
    assert 'self.setIconSize(QSize(24, 24))' in legacy


def test_phase328_esc_returns_to_dashboard_from_application_scope():
    src = read('alrajhi_client/views/main_window.py')
    assert 'self.esc_shortcut.setContext(Qt.ApplicationShortcut)' in src
    assert 'self.esc_shortcut.activated.connect(self._return_to_dashboard_from_escape)' in src
    assert 'def _return_to_dashboard_from_escape(self):' in src
    assert "self.switch_page('dashboard')" in src


def test_phase328_pos_warehouse_and_cashbox_share_one_row():
    src = read('alrajhi_client/views/widgets/pos_widget.py')
    assert 'Phase 328: keep POS discharge warehouse and cashbox in one' in src
    assert 'operation_row.addWidget(QLabel(translate("issue_warehouse")))' in src
    assert 'operation_row.addWidget(QLabel(translate("cashbox")))' in src
    assert 'layout.addLayout(operation_row)' in src
    assert 'layout.addLayout(wh_row)' not in src
    assert 'layout.addLayout(shift_row)' not in src


def test_phase328_transaction_header_footer_more_compact_for_sale_and_purchase():
    src = read('alrajhi_client/features/transactions/transaction_document_tab.py')
    totals = read('alrajhi_client/features/transactions/components/transaction_totals_panel.py')
    qss = read('alrajhi_client/theme/qss.py')
    assert 'inline_header.setObjectName("TransactionInlineHeaderBar")' in src
    assert 'header.setSpacing(4)' in src
    assert 'self.party_combo.setMinimumWidth(120)' in src
    assert 'self.warehouse_combo.setMinimumWidth(118)' in src
    assert 'self.search_input.setMinimumWidth(135)' in src
    assert 'label.setMaximumWidth(76)' in src
    assert 'side_layout.addWidget(self.notes, 3)' in src
    assert 'side_layout.addWidget(self.totals_panel, 7)' in src
    assert 'summary.setContentsMargins(8, 6, 8, 6)' in totals
    assert 'payment.setContentsMargins(8, 6, 8, 6)' in totals
    assert 'Phase 326/328: compact one-row transaction header' in qss


def test_phase328_release_gate_registered_and_documented():
    gate = read('alrajhi_client/workspace/quality/release_gate_contract.py')
    assert 'dashboard_pos_transaction_ux_polish' in gate
    assert 'tests/test_phase328_dashboard_pos_transaction_ux_polish.py' in gate
    assert (ROOT / 'PHASE328_DASHBOARD_POS_TRANSACTION_UX_POLISH.md').exists()
