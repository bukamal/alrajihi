# -*- coding: utf-8 -*-
"""Column schema and presets for the materials workspace grid."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from i18n import translate


@dataclass(frozen=True)
class MaterialListColumn:
    key: str
    title_key: str
    required: bool = False
    default_width: int = 120


MATERIAL_COLUMNS: List[MaterialListColumn] = [
    MaterialListColumn('name', 'material_list_column_name', True, 220),
    MaterialListColumn('barcode', 'material_list_column_barcode', False, 150),
    MaterialListColumn('category', 'material_list_column_category', False, 150),
    MaterialListColumn('item_type', 'material_list_column_type', False, 120),
    MaterialListColumn('quantity', 'material_list_column_opening_qty', False, 110),
    MaterialListColumn('unit', 'material_list_column_unit', False, 90),
    MaterialListColumn('sold_quantity', 'material_list_column_sold_qty', False, 110),
    MaterialListColumn('available_quantity', 'material_list_column_available_qty', True, 130),
    MaterialListColumn('stock_status', 'material_list_column_stock_status', False, 120),
    MaterialListColumn('reorder_level', 'material_list_column_reorder_level', False, 120),
    MaterialListColumn('available_total', 'material_list_column_stock_value', False, 130),
    MaterialListColumn('unit_cost', 'material_list_column_unit_cost', False, 120),
]

MATERIAL_REQUIRED_KEYS = {c.key for c in MATERIAL_COLUMNS if c.required}

MATERIAL_PRESETS: Dict[str, List[str]] = {
    'compact': ['name', 'barcode', 'available_quantity', 'unit', 'stock_status'],
    'cashier': ['name', 'barcode', 'available_quantity', 'unit'],
    'warehouse': ['name', 'barcode', 'category', 'item_type', 'quantity', 'unit', 'available_quantity', 'stock_status', 'reorder_level'],
    'accountant': ['name', 'category', 'item_type', 'available_quantity', 'available_total', 'unit_cost'],
    'manager': [c.key for c in MATERIAL_COLUMNS],
}

PRESET_TITLE_KEYS = {
    'compact': 'material_preset_compact',
    'cashier': 'material_preset_cashier',
    'warehouse': 'material_preset_warehouse',
    'accountant': 'material_preset_accountant',
    'manager': 'material_preset_manager',
}


def material_column_keys() -> List[str]:
    return [c.key for c in MATERIAL_COLUMNS]


def material_display_headers() -> List[str]:
    return [translate(c.title_key) for c in MATERIAL_COLUMNS]


def material_preset_label(name: str) -> str:
    return translate(PRESET_TITLE_KEYS.get(name, name))


def material_visible_keys_for_preset(name: str) -> List[str]:
    keys = MATERIAL_PRESETS.get(name) or MATERIAL_PRESETS['manager']
    merged = list(dict.fromkeys(list(MATERIAL_REQUIRED_KEYS) + list(keys)))
    return [key for key in material_column_keys() if key in merged]
