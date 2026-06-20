# -*- coding: utf-8 -*-
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_return_list_widgets_open_editor_on_double_click():
    text = _read("alrajhi_client/views/widgets/returns_widget.py")
    assert text.count("self.table.doubleClicked.connect(self.edit_return_from_index)") >= 2
    assert "def edit_return_from_index(self, index):" in text
    assert "main.open_return_document('sale', return_id=rid, return_data=data)" in text
    assert "main.open_return_document('purchase', return_id=rid, return_data=data)" in text


def test_return_list_printing_uses_display_currency_payload_not_raw_storage_amounts():
    text = _read("alrajhi_client/views/widgets/returns_widget.py")
    assert "def _ret_list_return_print_payload" in text
    assert "stored monetary fields to the active display currency" in text
    assert "currency.convert(_ret_dec(value), source_currency" in text
    assert "'display_currency': display_code" in text
    assert "'currency': display_code" in text
    assert "'unit_price': str(unit_price_display)" in text
    assert "'line_total': str(line_total_display)" in text
    assert "'total': str(total_display)" in text
    assert "data = _ret_list_return_print_payload(data, self._row_data(), 'sale')" in text
    assert "data = _ret_list_return_print_payload(data, self._row_data(), 'purchase')" in text


def test_return_print_template_prefers_return_number_and_localizes_credit_only():
    text = _read("alrajhi_client/printing/print_templates.py")
    assert 'payload.get("return_no")' in text
    assert "'credit_only': 'payment_credit'" in text


def test_return_list_selection_handles_source_rows_for_filtered_tables():
    text = _read("alrajhi_client/views/widgets/returns_widget.py")
    assert "def _selected_source_row(self):" in text
    assert "rows = self.table.selected_source_rows()" in text
    assert "proxy.mapToSource(index)" in text
    assert "def _row_data(self, row=None):" in text
