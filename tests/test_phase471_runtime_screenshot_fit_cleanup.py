# -*- coding: utf-8 -*-
"""Phase471 guards for runtime screenshot fit cleanup."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_transaction_header_uses_three_row_stable_layout_and_vertical_fields():
    src = read("alrajhi_client/features/transactions/transaction_document_tab.py")
    assert 'transactionHeaderPhase", "471"' in src
    assert 'tools_row = QHBoxLayout()' in src
    assert 'TransactionDocumentToolsRow' in src
    assert 'header.addLayout(tools_row)' in src
    assert 'transactionHeaderFieldPhase", "471"' in src
    assert 'layout = QVBoxLayout(box)' in src
    assert 'label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)' in src
    assert 'box.setMinimumHeight(62)' in src


def test_transaction_bottom_actions_are_responsive_not_overlapping():
    src = read("alrajhi_client/features/transactions/components/transaction_bottom_actions.py")
    assert 'transactionActionLayoutPhase", "471"' in src
    assert 'QSizePolicy.Expanding' in src
    assert 'max_per_row = 5  # Phase471' in src
    assert 'button.setMinimumWidth(118)' in src


def test_restaurant_footer_total_has_own_row_to_prevent_clipping():
    src = read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    assert 'restaurantOperationalCleanupPhase", 471' in src
    assert 'restaurantFooterLayoutPhase", "471"' in src
    assert 'footer_layout = QVBoxLayout(footer)' in src
    assert 'restaurantSimpleFooterActions' in src
    assert 'footer_layout.addWidget(self.total_label)' in src
    assert 'footer_layout.addLayout(action_row)' in src


def test_table_toolbar_export_button_short_label():
    src = read("alrajhi_client/views/widgets/components/table_toolbar.py")
    assert 'self.export_btn = QPushButton("Excel")' in src
    assert 'self.export_btn.setToolTip(translate("export_excel"))' in src


def test_phase471_qss_contracts_exist():
    qss = read("alrajhi_client/theme/qss.py")
    assert 'Phase471: runtime screenshot fit' in qss
    assert 'QFrame#TransactionDocumentHeaderShell[transactionHeaderPhase="471"]' in qss
    assert 'QWidget#TransactionBottomActionBar[transactionActionLayoutPhase="471"]' in qss
    assert 'QWidget#restaurantSimplePOSWidget[restaurantOperationalCleanupPhase="471"] QFrame#restaurantSimpleFooter[restaurantFooterLayoutPhase="471"]' in qss
