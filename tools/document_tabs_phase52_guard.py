#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Phase 52 manufacturing document tabs.

BOMs and production orders should route through workspace document tabs while
keeping persistence behind ManufacturingService and keeping item-unit ids in BOM
lines.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / 'alrajhi_client' / 'features' / 'manufacturing' / '__init__.py',
    ROOT / 'alrajhi_client' / 'features' / 'manufacturing' / 'bom_document_tab.py',
    ROOT / 'alrajhi_client' / 'features' / 'manufacturing' / 'production_order_document_tab.py',
    ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'manufacturing_widget.py',
    ROOT / 'alrajhi_client' / 'views' / 'main_window.py',
]


def main() -> int:
    errors: list[str] = []
    for path in FILES:
        if not path.exists():
            errors.append(f'missing {path.relative_to(ROOT)}')
            continue
        try:
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        except SyntaxError as exc:
            errors.append(f'syntax error in {path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}')

    bom_text = (ROOT / 'alrajhi_client/features/manufacturing/bom_document_tab.py').read_text(encoding='utf-8')
    order_text = (ROOT / 'alrajhi_client/features/manufacturing/production_order_document_tab.py').read_text(encoding='utf-8')
    widget_text = (ROOT / 'alrajhi_client/views/widgets/manufacturing_widget.py').read_text(encoding='utf-8')
    main_text = (ROOT / 'alrajhi_client/views/main_window.py').read_text(encoding='utf-8')
    bom_dialog_text = (ROOT / 'alrajhi_client/views/dialogs/bom_dialog.py').read_text(encoding='utf-8')

    for token in (
        'class BomDocumentTab(DialogDocumentTab)',
        'BOMDialog',
        "document_type='bom'",
    ):
        if token not in bom_text:
            errors.append(f'BOM document tab missing token: {token}')

    for token in (
        'class ProductionOrderDocumentTab(DialogDocumentTab)',
        'class ProductionOrderDetailsTab(DialogDocumentTab)',
        'ProductionOrderDialog',
        'ProductionDetailsDialog',
    ):
        if token not in order_text:
            errors.append(f'Production document tab missing token: {token}')

    for token in (
        'def open_bom_document',
        'def open_production_order_document',
        'def open_production_order_details',
        'from features.manufacturing import BomDocumentTab',
        'from features.manufacturing import ProductionOrderDocumentTab',
        'from features.manufacturing import ProductionOrderDetailsTab',
    ):
        if token not in main_text:
            errors.append(f'main_window missing manufacturing document integration: {token}')

    for token in (
        'main.open_bom_document()',
        'main.open_bom_document(bom_id=bom_id)',
        'main.open_production_order_document()',
        'main.open_production_order_details(order_id=order_id)',
    ):
        if token not in widget_text:
            errors.append(f'ManufacturingWidget still lacks document tab route: {token}')

    if "'unit_id': unit_id" not in bom_dialog_text or "'unit_id': l.get('unit_id')" not in bom_dialog_text:
        errors.append('BOM dialog does not preserve item unit_id in component lines')

    if errors:
        print('Phase 52 manufacturing document tabs guard failed:')
        for error in errors:
            print(f' - {error}')
        return 1
    print('Phase 52 manufacturing document tabs guard passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
