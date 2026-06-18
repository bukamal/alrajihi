# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase63_invoice_quick_quantity_and_status_are_present():
    text = (ROOT / 'alrajhi_client/views/dialogs/invoice_dialog.py').read_text(encoding='utf-8')
    assert 'InvoiceQuickQtySpin' in text
    assert '_quick_add_qty' in text
    assert 'Qt.Key_F6' in text
    assert 'InvoiceGridStatus' in text
    assert 'update_invoice_grid_status' in text


def test_phase63_invoice_line_validation_feedback_is_in_model():
    text = (ROOT / 'alrajhi_client/views/dialogs/invoice_dialog.py').read_text(encoding='utf-8')
    assert 'row_validation_message' in text
    assert 'invalid_rows' in text
    assert 'Qt.BackgroundRole' in text
    assert 'Qt.ToolTipRole' in text
    assert 'invoice_line_unresolved_item' in text
