#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f'phase176_pos_visual_grid_guard failed: {message}')


pos_widget = read('alrajhi_client/views/widgets/pos_widget.py')
require('POSLineGrid' in pos_widget, 'POSWidget must use POSLineGrid')
require('POSLineModel' in pos_widget, 'POSWidget must use POSLineModel')
require('EditableSmartGrid' not in pos_widget, 'POSWidget must not use legacy EditableSmartGrid cart table')
require('QTableWidgetItem' not in pos_widget, 'POSWidget must not manually fill QTableWidgetItem rows')
require('visible_keys_for_preset' in pos_widget, 'POSWidget must apply shared column presets')
require('def on_preset_changed' in pos_widget, 'POS preset workflow missing')
require('currentRow()' not in pos_widget, 'POS row removal must use model/grid selection, not QTableWidget currentRow')

schema = read('alrajhi_client/features/pos/pos_line_schema.py')
require('TransactionColumn' in schema, 'POS line schema must be based on TransactionColumn')
require('pos_column_base_qty' in schema, 'POS schema must expose base quantity for unit barcodes')
require('pos_column_barcode_scope' in schema, 'POS schema must expose item/unit barcode scope')

model = read('alrajhi_client/features/pos/pos_line_model.py')
require('QAbstractTableModel' in model, 'POSLineModel must be a Qt table model')
require('POSCart' in model and 'POSLine' in model, 'POSLineModel must render POSCart/POSLine')
require('line_at' in model, 'POSLineModel should provide row-to-line lookup')

grid = read('alrajhi_client/features/pos/pos_line_grid.py')
require('TransactionLineGrid' in grid, 'POSLineGrid must reuse the shared TransactionLineGrid engine')
require('apply_density' in grid, 'POSLineGrid must expose touch density application')

prefs = read('alrajhi_client/features/pos/pos_preferences.py')
require('def preset' in prefs and 'def save_preset' in prefs, 'POSPreferences must persist preset per user/branch/profile')

translator = read('alrajhi_client/i18n/translator.py')
for key in ('pos_column_base_qty', 'pos_column_barcode_scope', 'pos_barcode_scope_item', 'pos_barcode_scope_unit'):
    require(key in translator, f'missing translation key {key}')

print('phase176_pos_visual_grid_guard passed')
