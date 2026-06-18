# -*- coding: utf-8 -*-
"""Workspace schemas and presets for inventory / warehouse screens.

Phase 195 brings the warehouse workspace in line with the professional table
pattern used for materials, transactions, POS, restaurant, and manufacturing:
stable column keys, translated labels, practical presets, density support, and
source-row-safe table selections.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from i18n import translate


@dataclass(frozen=True)
class InventoryWorkspaceColumn:
    key: str
    title_key: str
    default_visible: bool = True
    compact_visible: bool = True

    @property
    def title(self) -> str:
        return translate(self.title_key)


def warehouse_columns() -> list[InventoryWorkspaceColumn]:
    return [
        InventoryWorkspaceColumn('name', 'warehouse', True, True),
        InventoryWorkspaceColumn('code', 'warehouse_code', True, True),
        InventoryWorkspaceColumn('branch_name', 'branch', True, False),
        InventoryWorkspaceColumn('location', 'location', True, False),
        InventoryWorkspaceColumn('item_count', 'items_count', True, False),
        InventoryWorkspaceColumn('total_qty', 'total_quantities', True, False),
        InventoryWorkspaceColumn('is_default', 'default', True, False),
        InventoryWorkspaceColumn('status', 'status', True, True),
        InventoryWorkspaceColumn('notes', 'notes', True, False),
    ]


def balance_columns() -> list[InventoryWorkspaceColumn]:
    return [
        InventoryWorkspaceColumn('warehouse_name', 'warehouse', True, True),
        InventoryWorkspaceColumn('item_name', 'item', True, True),
        InventoryWorkspaceColumn('barcode', 'barcode', True, False),
        InventoryWorkspaceColumn('quantity', 'quantity', True, True),
        InventoryWorkspaceColumn('unit', 'unit', True, True),
        InventoryWorkspaceColumn('stock_status', 'inventory_stock_status', True, True),
        InventoryWorkspaceColumn('average_cost', 'unit_cost', True, False),
        InventoryWorkspaceColumn('stock_value', 'stock_value', True, False),
        InventoryWorkspaceColumn('updated_at', 'last_update', True, False),
    ]


def movement_columns() -> list[InventoryWorkspaceColumn]:
    return [
        InventoryWorkspaceColumn('date', 'date', True, True),
        InventoryWorkspaceColumn('warehouse_name', 'warehouse', True, True),
        InventoryWorkspaceColumn('item_name', 'item', True, True),
        InventoryWorkspaceColumn('type', 'type', True, True),
        InventoryWorkspaceColumn('quantity', 'quantity', True, True),
        InventoryWorkspaceColumn('unit_name', 'unit', True, True),
        InventoryWorkspaceColumn('base_qty', 'inventory_transfer_column_base_qty', True, False),
        InventoryWorkspaceColumn('unit_cost', 'unit_cost', True, False),
        InventoryWorkspaceColumn('reference', 'reference', True, False),
        InventoryWorkspaceColumn('notes', 'notes', True, False),
    ]


def transfer_columns() -> list[InventoryWorkspaceColumn]:
    return [
        InventoryWorkspaceColumn('transfer_no', 'reference', True, True),
        InventoryWorkspaceColumn('created_at', 'date', True, True),
        InventoryWorkspaceColumn('item_name', 'item', True, True),
        InventoryWorkspaceColumn('from_warehouse', 'from_warehouse_clean', True, True),
        InventoryWorkspaceColumn('to_warehouse', 'to_warehouse_clean', True, True),
        InventoryWorkspaceColumn('quantity', 'quantity', True, True),
        InventoryWorkspaceColumn('unit_name', 'unit', True, True),
        InventoryWorkspaceColumn('base_qty', 'inventory_transfer_column_base_qty', True, False),
        InventoryWorkspaceColumn('unit_cost', 'unit_cost', True, False),
        InventoryWorkspaceColumn('status', 'status', True, True),
        InventoryWorkspaceColumn('notes', 'notes', True, False),
    ]


def inventory_workspace_preset_names() -> list[str]:
    return ['compact', 'warehouse', 'accountant', 'manager']


def inventory_workspace_preset_title(preset: str) -> str:
    return translate(f'inventory_workspace_preset_{preset}')


def columns_for(kind: str) -> list[InventoryWorkspaceColumn]:
    mapping = {
        'warehouses': warehouse_columns,
        'balances': balance_columns,
        'movements': movement_columns,
        'transfers': transfer_columns,
    }
    return mapping.get(kind, warehouse_columns)()


def visible_keys_for(kind: str, preset: str) -> set[str]:
    preset = (preset or 'manager').strip().lower()
    all_keys = {col.key for col in columns_for(kind)}
    presets = {
        'warehouses': {
            'compact': {'name', 'code', 'status'},
            'warehouse': {'name', 'code', 'location', 'item_count', 'total_qty', 'status'},
            'accountant': {'name', 'code', 'branch_name', 'item_count', 'total_qty', 'is_default', 'status'},
            'manager': all_keys,
        },
        'balances': {
            'compact': {'warehouse_name', 'item_name', 'quantity', 'unit', 'stock_status'},
            'warehouse': {'warehouse_name', 'item_name', 'barcode', 'quantity', 'unit', 'stock_status', 'updated_at'},
            'accountant': {'warehouse_name', 'item_name', 'quantity', 'unit', 'average_cost', 'stock_value'},
            'manager': all_keys,
        },
        'movements': {
            'compact': {'date', 'warehouse_name', 'item_name', 'type', 'quantity'},
            'warehouse': {'date', 'warehouse_name', 'item_name', 'type', 'quantity', 'reference'},
            'accountant': {'date', 'warehouse_name', 'item_name', 'type', 'quantity', 'unit_cost', 'reference'},
            'manager': all_keys,
        },
        'transfers': {
            'compact': {'transfer_no', 'created_at', 'item_name', 'from_warehouse', 'to_warehouse', 'quantity', 'status'},
            'warehouse': {'transfer_no', 'created_at', 'item_name', 'from_warehouse', 'to_warehouse', 'quantity', 'unit_name', 'base_qty', 'status'},
            'accountant': {'transfer_no', 'created_at', 'item_name', 'from_warehouse', 'to_warehouse', 'quantity', 'base_qty', 'unit_cost', 'status'},
            'manager': all_keys,
        },
    }
    return set(presets.get(kind, {}).get(preset, all_keys))


def headers_and_keys(columns: Iterable[InventoryWorkspaceColumn]) -> tuple[list[str], list[str]]:
    cols = list(columns)
    return [col.title for col in cols], [col.key for col in cols]
