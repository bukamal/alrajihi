# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_invoice_edit_delete_resolves_source_model_and_selection():
    text = _read("alrajhi_client/views/widgets/invoices_widget.py")
    assert "def _source_model_for_invoice_type(self, inv_type):" in text
    assert "def _source_row_from_index(self, inv_type, index):" in text
    assert "def _selected_invoice_source_row(self, inv_type):" in text
    assert "table.selected_source_rows()" in text
    assert "proxy.mapToSource(index)" in text
    assert "return self._invoice_id_at_source_row(inv_type, self._selected_invoice_source_row(inv_type))" in text


def test_invoice_buttons_open_and_delete_correct_documents():
    text = _read("alrajhi_client/views/widgets/invoices_widget.py")
    assert "self.sales_toolbar.editRequested.connect(lambda: self.edit_selected_invoice('sale'))" in text
    assert "self.purchases_toolbar.editRequested.connect(lambda: self.edit_selected_invoice('purchase'))" in text
    assert "self.sales_toolbar.deleteRequested.connect(lambda: self.delete_selected_invoice('sale'))" in text
    assert "self.purchases_toolbar.deleteRequested.connect(lambda: self.delete_selected_invoice('purchase'))" in text
    assert "main.open_quick_invoice(inv_type, invoice_id=inv_id)" in text
    assert "invoice_service.has_linked_vouchers(inv_id)" in text
    assert "invoice_service.has_linked_returns(inv_id)" in text
    assert "self.refresh_tab(inv_type, reset_page=True)" in text


def test_return_buttons_follow_selection_changes_not_blind_clicks():
    text = _read("alrajhi_client/views/widgets/returns_widget.py")
    assert text.count("self.toolbar.editRequested.connect(self.edit_selected)") >= 2
    assert text.count("self.toolbar.deleteRequested.connect(self.cancel_selected)") >= 2
    assert text.count("def _connect_table_selection(self):") >= 2
    assert text.count("selectionChanged.connect(self._update_return_actions)") >= 2
    assert "clicked.connect(lambda *_: self.toolbar.set_delete_enabled(True))" not in text
    assert "clicked.connect(lambda *_: self.toolbar.set_edit_enabled(True))" not in text


def test_return_edit_delete_permissions_and_source_row_mapping():
    text = _read("alrajhi_client/views/widgets/returns_widget.py")
    assert "from core.services.permission_service import permission_service" in text
    assert text.count("permission_service.ACTION_EDIT_RETURNS") >= 4
    assert text.count("permission_service.ACTION_DELETE") >= 4
    assert text.count("if not hasattr(self, 'model'):") >= 2
    assert text.count("proxy.mapToSource(index)") >= 2
    assert "show_toast(translate('select_return_first')" in text


def test_phase387_contract_and_translations_exist():
    contract = _read("alrajhi_client/workspace/quality/invoice_return_list_actions_contract.py")
    translator = _read("alrajhi_client/i18n/translator.py")
    assert "INVOICE_RETURN_LIST_ACTION_PHASE = 387" in contract
    assert "REQUIRED_ACTION_GUARANTEES" in contract
    assert "delete_invoice_linked_returns_message" in translator
