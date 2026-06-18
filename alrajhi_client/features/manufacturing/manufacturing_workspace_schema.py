# -*- coding: utf-8 -*-
"""Column schemas and presets for the manufacturing workspace.

Phase 193 moves the main manufacturing lists toward the same professional
workspace behavior used by items, invoices, POS, and restaurant screens: stable
column keys, translated labels, user-scoped layouts through SmartTableView, and
small practical presets.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from features.manufacturing.i18n import tr


@dataclass(frozen=True)
class WorkspaceColumn:
    key: str
    title_key: str
    default_visible: bool = True
    compact_visible: bool = True

    @property
    def title(self) -> str:
        return tr(self.title_key)


def bom_columns() -> list[WorkspaceColumn]:
    return [
        WorkspaceColumn('product', 'product', True, True),
        WorkspaceColumn('quantity', 'quantity', True, True),
        WorkspaceColumn('components_count', 'manufacturing_components_count', True, False),
        WorkspaceColumn('created_at', 'created_at', True, False),
    ]


def production_order_columns() -> list[WorkspaceColumn]:
    return [
        WorkspaceColumn('order_number', 'order_number', True, True),
        WorkspaceColumn('product', 'product', True, True),
        WorkspaceColumn('planned_qty', 'planned_qty', True, True),
        WorkspaceColumn('produced_qty', 'produced_qty', True, False),
        WorkspaceColumn('status', 'status', True, True),
        WorkspaceColumn('raw_warehouse', 'raw_warehouse', True, False),
        WorkspaceColumn('output_warehouse', 'output_warehouse', True, False),
        WorkspaceColumn('start_date', 'start_date', True, False),
    ]


def workspace_preset_names() -> list[str]:
    return ['compact', 'planner', 'warehouse', 'manager']


def workspace_preset_title(preset: str) -> str:
    return tr(f'manufacturing_workspace_preset_{preset}')


def visible_keys_for(kind: str, preset: str) -> set[str]:
    preset = (preset or 'manager').strip().lower()
    if kind == 'bom':
        mapping = {
            'compact': {'product', 'quantity'},
            'planner': {'product', 'quantity', 'components_count'},
            'warehouse': {'product', 'quantity', 'components_count'},
            'manager': {c.key for c in bom_columns()},
        }
        return set(mapping.get(preset, mapping['manager']))
    mapping = {
        'compact': {'order_number', 'product', 'planned_qty', 'status'},
        'planner': {'order_number', 'product', 'planned_qty', 'produced_qty', 'status', 'start_date'},
        'warehouse': {'order_number', 'product', 'planned_qty', 'status', 'raw_warehouse', 'output_warehouse'},
        'manager': {c.key for c in production_order_columns()},
    }
    return set(mapping.get(preset, mapping['manager']))


def headers_and_keys(columns: Iterable[WorkspaceColumn]) -> tuple[list[str], list[str]]:
    cols = list(columns)
    return [c.title for c in cols], [c.key for c in cols]
