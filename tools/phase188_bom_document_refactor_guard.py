# -*- coding: utf-8 -*-
"""Phase 188 guard: BOM is a real document tab with unit-aware grid."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def require(condition: bool, message: str) -> None:
    if not condition:
        print(f'FAIL: {message}')
        sys.exit(1)


def main() -> None:
    bom_tab = read('alrajhi_client/features/manufacturing/bom_document_tab.py')
    require('class BomDocumentTab(BaseDocumentTab)' in bom_tab, 'BomDocumentTab must inherit BaseDocumentTab, not DialogDocumentTab')
    require('DialogDocumentTab' in bom_tab and 'LegacyBomDocumentTab' in bom_tab, 'legacy fallback wrapper must remain explicit')
    require('BomComponentsGrid' in bom_tab and 'BomComponentsModel' in bom_tab, 'BOM tab must use professional grid/model')
    require('barcode_input_service.lookup_entry' in bom_tab, 'BOM component lookup must use unified barcode/manual input service')
    require('manufacturing_operation_policy.OP_BOM_CREATE' in bom_tab, 'BOM create permission must be checked')
    require('manufacturing_operation_policy.OP_BOM_EDIT' in bom_tab, 'BOM edit permission must be checked')

    model = read('alrajhi_client/features/manufacturing/grids/bom_components_model.py')
    for token in ('set_item(', 'set_unit(', 'unit_options_for_row', 'conversion_factor', 'base_qty', 'payload_lines'):
        require(token in model, f'BomComponentsModel missing {token}')
    require('catalog_service.item_units' in model, 'BOM model must load material unit options through catalog_service')

    grid = read('alrajhi_client/features/manufacturing/grids/bom_components_grid.py')
    require('TransactionLineGrid' in grid, 'BOM components grid must reuse TransactionLineGrid behaviour')
    require('price_key_provider=lambda: \'purchase_price\'' in grid or 'purchase_price' in grid, 'BOM grid must use cost/purchase price context')

    schema = read('alrajhi_client/features/manufacturing/grids/manufacturing_column_schema.py')
    for key in ('item', 'unit', 'qty', 'base_qty', 'waste_percent', 'unit_cost', 'total_cost'):
        require(f"'{key}'" in schema, f'BOM schema missing {key}')

    translations = read('alrajhi_client/i18n/translator.py')
    for key in ('manufacturing_component_search_placeholder', 'manufacturing_bom_cost_summary', 'manufacturing_column_waste_percent'):
        require(key in translations, f'missing i18n key {key}')

    print('phase188_bom_document_refactor_guard passed')


if __name__ == '__main__':
    main()
