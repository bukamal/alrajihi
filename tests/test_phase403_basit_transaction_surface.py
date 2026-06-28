# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_transaction_document_is_tagged_for_basit_surface():
    src = read("alrajhi_client/features/transactions/transaction_document_tab.py")
    assert 'self.setProperty("basitInspired", True)' in src
    assert 'self.setProperty("basitTransactionDocument", True)' in src
    assert 'inline_header.setProperty("basitToolbar", True)' in src
    assert 'self.grid.setProperty("basitTable", True)' in src
    assert 'self.grid.setProperty("basitTransactionGrid", True)' in src
    assert 'self.side_panel.setProperty("basitTotalFooter", True)' in src


def test_transaction_header_buttons_use_basit_toolbar_role():
    src = read("alrajhi_client/features/transactions/transaction_document_tab.py")
    assert src.count('setProperty("basitToolbarButton", True)') >= 5
    for label in ['tr("add")', 'tr("transaction_save_shortcut")', 'tr("transaction_columns")', 'tr("transaction_reset_view")']:
        assert label in src


def test_transaction_totals_and_payment_frames_use_basit_roles():
    src = read("alrajhi_client/features/transactions/components/transaction_totals_panel.py")
    assert 'self.summary_frame.setProperty("basitPanel", True)' in src
    assert 'self.summary_frame.setProperty("basitTransactionSummary", True)' in src
    assert 'self.payment_frame.setProperty("basitPanel", True)' in src
    assert 'self.payment_frame.setProperty("basitTransactionPayment", True)' in src
    assert 'widget.setProperty("basitTotal", title_key == "transaction_net_total")' in src
    assert src.count('setProperty("basitToolbarButton", True)') >= 2


def test_qss_contains_basit_transaction_invoice_rules():
    qss = read("alrajhi_client/theme/qss.py")
    assert "Phase403: Basit-inspired invoices and returns" in qss
    assert 'QFrame#TransactionInlineHeaderBar[basitToolbar="true"]' in qss
    assert 'QTableView[basitTransactionGrid="true"]' in qss
    assert 'QFrame#TransactionHorizontalSummaryFrame[basitTransactionSummary="true"]' in qss
    assert 'QLabel#TransactionSummaryValue[basitTotal="true"]' in qss


def test_quality_contract_documents_transaction_surface():
    contract = read("alrajhi_client/workspace/quality/basit_transaction_surface_contract.py")
    assert "BASIT_TRANSACTION_SURFACE_CONTRACT" in contract
    assert "Transaction documents are tagged basitInspired" in contract
    assert "Net total is emphasized" in contract
