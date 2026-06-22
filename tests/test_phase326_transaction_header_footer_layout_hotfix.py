# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase326_transaction_header_is_single_inline_row_above_grid():
    src = read("alrajhi_client/features/transactions/transaction_document_tab.py")
    assert "TransactionInlineHeaderBar" in src
    assert "def _inline_header_field" in src
    assert "root.addWidget(inline_header)" in src
    assert "header = QHBoxLayout(inline_header)" in src
    assert "header.addWidget(self._inline_header_field" in src
    assert "root.addLayout(header)" not in src
    assert "header.addWidget(self.presets_combo)" in src
    assert "header.addWidget(save_btn)" in src


def test_phase326_invoice_footer_summary_is_horizontal_and_notes_compact():
    tab = read("alrajhi_client/features/transactions/transaction_document_tab.py")
    panel = read("alrajhi_client/features/transactions/components/transaction_totals_panel.py")
    assert "self.notes.setMaximumHeight(78)" in tab
    assert "self.notes.setMinimumHeight(72)" in tab
    assert "side_layout.addWidget(self.notes, 2)" in tab
    assert "side_layout.addWidget(self.totals_panel, 5)" in tab
    assert "TransactionHorizontalSummaryFrame" in panel
    assert "TransactionHorizontalPaymentFrame" in panel
    assert "layout = QHBoxLayout(self)" in panel
    assert "summary.addWidget(caption, 0, col)" in panel
    assert "summary.addWidget(widget, 1, col)" in panel
    assert "payment = QHBoxLayout(self.payment_frame)" in panel


def test_phase326_material_editor_does_not_render_new_material_identity_card():
    editor = read("alrajhi_client/features/items/item_editor_tab.py")
    assert "Do not render the top identity card" in editor
    assert "self.header_frame = self._build_header()" in editor
    assert "self.header_frame.setVisible(False)" in editor
    assert "root.addWidget(self._build_header())" not in editor


def test_phase326_qss_and_release_gate_registered():
    qss = read("alrajhi_client/theme/qss.py")
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "TransactionInlineHeaderBar" in qss
    assert "TransactionHorizontalSummaryFrame" in qss
    assert "TransactionSummaryValue" in qss
    assert '(326, "TRANSACTION_HEADER_FOOTER_LAYOUT_HOTFIX")' in gate
    assert '(326, "transaction_header_footer_layout_hotfix")' in gate
    assert "tests/test_phase326_transaction_header_footer_layout_hotfix.py" in gate
