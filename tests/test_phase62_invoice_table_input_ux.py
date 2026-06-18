# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase62_invoice_grid_shortcuts_are_present():
    text = (ROOT / 'alrajhi_client/views/dialogs/invoice_dialog.py').read_text(encoding='utf-8')
    assert 'invoice_grid_shortcuts_label' in text
    assert 'Qt.Key_Insert' in text
    assert 'duplicate_selected_line' in text
    assert 'Qt.Key_F4' in text
    assert 'Qt.Key_L' in text


def test_phase62_smart_table_enterprise_shortcuts_and_density():
    text = (ROOT / 'alrajhi_client/ui/smart_table_view.py').read_text(encoding='utf-8')
    assert '_install_enterprise_shortcuts' in text
    assert 'Ctrl+Shift+C' in text
    assert 'Ctrl+Alt+F' in text
    assert 'Ctrl+Shift+S' in text
    assert 'set_density' in text
    assert 'visible_columns' in text
