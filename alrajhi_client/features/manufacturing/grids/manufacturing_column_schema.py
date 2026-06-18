# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass

from features.manufacturing.i18n import tr


@dataclass(frozen=True)
class ManufacturingColumn:
    key: str
    title_key: str
    required: bool = False
    default_visible: bool = True
    compact_visible: bool = False
    width: int = 120
    stretch: bool = False
    editable: bool = True
    numeric: bool = False

    @property
    def title(self) -> str:
        return tr(self.title_key)


def bom_components_schema() -> list[ManufacturingColumn]:
    return [
        ManufacturingColumn('row', '#', True, True, True, 44, editable=False),
        ManufacturingColumn('barcode', 'transaction_column_barcode', False, True, False, 125),
        ManufacturingColumn('item', 'transaction_column_item', True, True, True, 260, True),
        ManufacturingColumn('unit', 'transaction_column_unit', False, True, True, 95),
        ManufacturingColumn('qty', 'manufacturing_column_component_qty', True, True, True, 110, numeric=True),
        ManufacturingColumn('base_qty', 'manufacturing_column_base_qty', False, True, False, 115, numeric=True, editable=False),
        ManufacturingColumn('waste_percent', 'manufacturing_column_waste_percent', False, True, False, 115, numeric=True),
        ManufacturingColumn('unit_cost', 'manufacturing_column_unit_cost', False, True, False, 120, numeric=True),
        ManufacturingColumn('total_cost', 'manufacturing_column_total_cost', False, True, True, 130, numeric=True, editable=False),
        ManufacturingColumn('notes', 'transaction_column_notes', False, True, False, 190),
    ]


def production_required_materials_schema() -> list[ManufacturingColumn]:
    return [
        ManufacturingColumn('row', '#', True, True, True, 44, editable=False),
        ManufacturingColumn('item', 'transaction_column_item', True, True, True, 260, True, editable=False),
        ManufacturingColumn('unit', 'transaction_column_unit', False, True, True, 100, editable=False),
        ManufacturingColumn('required_qty', 'manufacturing_column_required_qty', True, True, True, 120, numeric=True, editable=False),
        ManufacturingColumn('available_qty', 'manufacturing_column_available_qty', False, True, True, 120, numeric=True, editable=False),
        ManufacturingColumn('shortage_qty', 'manufacturing_column_shortage_qty', False, True, False, 120, numeric=True, editable=False),
        ManufacturingColumn('status', 'status', False, True, True, 110, editable=False),
        ManufacturingColumn('conversion_factor', 'manufacturing_column_conversion_factor', False, True, False, 130, numeric=True, editable=False),
        ManufacturingColumn('base_qty', 'manufacturing_column_base_qty', False, True, False, 120, numeric=True, editable=False),
    ]



def production_reservations_schema() -> list[ManufacturingColumn]:
    return [
        ManufacturingColumn('row', '#', True, True, True, 44, editable=False),
        ManufacturingColumn('item', 'transaction_column_item', True, True, True, 260, True, editable=False),
        ManufacturingColumn('unit', 'transaction_column_unit', False, True, True, 95, editable=False),
        ManufacturingColumn('reserved_qty', 'reserved', True, True, True, 120, numeric=True, editable=False),
        ManufacturingColumn('consumed_qty', 'consumed', False, True, True, 120, numeric=True, editable=False),
        ManufacturingColumn('remaining_qty', 'remaining', False, True, True, 120, numeric=True, editable=False),
        ManufacturingColumn('conversion_factor', 'manufacturing_column_conversion_factor', False, True, False, 130, numeric=True, editable=False),
        ManufacturingColumn('base_qty', 'manufacturing_column_base_qty', False, True, False, 120, numeric=True, editable=False),
    ]


def production_consumptions_schema() -> list[ManufacturingColumn]:
    return [
        ManufacturingColumn('row', '#', True, True, True, 44, editable=False),
        ManufacturingColumn('item', 'transaction_column_item', True, True, True, 260, True, editable=False),
        ManufacturingColumn('unit', 'transaction_column_unit', False, True, True, 95, editable=False),
        ManufacturingColumn('qty', 'consumed', True, True, True, 120, numeric=True, editable=False),
        ManufacturingColumn('unit_cost', 'manufacturing_column_unit_cost', False, True, False, 125, numeric=True, editable=False),
        ManufacturingColumn('total_cost', 'manufacturing_column_total_cost', False, True, True, 130, numeric=True, editable=False),
        ManufacturingColumn('date', 'date', False, True, False, 150, editable=False),
    ]


def production_outputs_schema() -> list[ManufacturingColumn]:
    return [
        ManufacturingColumn('row', '#', True, True, True, 44, editable=False),
        ManufacturingColumn('item', 'product', True, True, True, 260, True, editable=False),
        ManufacturingColumn('unit', 'transaction_column_unit', False, True, True, 95, editable=False),
        ManufacturingColumn('qty', 'produced_qty', True, True, True, 120, numeric=True, editable=False),
        ManufacturingColumn('unit_cost', 'manufacturing_column_unit_cost', False, True, False, 125, numeric=True, editable=False),
        ManufacturingColumn('total_cost', 'manufacturing_column_total_cost', False, True, True, 130, numeric=True, editable=False),
        ManufacturingColumn('date', 'date', False, True, False, 150, editable=False),
    ]
