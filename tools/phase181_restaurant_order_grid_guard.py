# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[phase181] {message}")


def main() -> None:
    widget = read('alrajhi_client/views/restaurant/restaurant_pos_widget.py')
    grid = read('alrajhi_client/features/restaurant/restaurant_order_grid.py')
    model = read('alrajhi_client/features/restaurant/restaurant_order_model.py')
    schema = read('alrajhi_client/features/restaurant/restaurant_order_schema.py')
    i18n = read('alrajhi_client/i18n/translator.py')

    require('QListWidget' not in widget and 'QListWidgetItem' not in widget, 'Restaurant POS must not use QListWidget for order lines')
    require('RestaurantOrderGrid' in widget, 'Restaurant POS must use RestaurantOrderGrid')
    require('RestaurantOrderModel' in widget, 'Restaurant POS must use RestaurantOrderModel')
    require('self.order_model.set_lines' in widget, 'Restaurant POS must reload lines through the model')
    require('class RestaurantOrderGrid(TransactionLineGrid)' in grid, 'RestaurantOrderGrid must reuse TransactionLineGrid')
    require('class RestaurantOrderModel(QAbstractTableModel)' in model, 'Restaurant order lines must use QAbstractTableModel')
    require('base_qty' in schema and 'barcode_scope' in schema and 'restaurant_column_status' in schema, 'Restaurant schema must include unit/barcode/status columns')
    require('pos_barcode_scope_unit' in model and 'restaurant.barcode_scope_menu' in model, 'Model must translate barcode scopes')
    for key in ('restaurant_column_modifiers', 'restaurant_column_status', 'restaurant_order_grid_unified'):
        require(key in i18n, f'Missing translation key: {key}')
    print('phase181 restaurant order grid guard: OK')


if __name__ == '__main__':
    main()
