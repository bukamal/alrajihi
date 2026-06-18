# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

def main():
    doc = read('alrajhi_client/features/inventory/documents/warehouse_document_tab.py')
    assert 'class WarehouseDocumentTab(BaseDocumentTab)' in doc
    assert 'warehouse_service.add_warehouse' in doc
    assert 'warehouse_service.update_warehouse' in doc
    assert 'inventory_operation_policy.OP_WAREHOUSE_CREATE' in doc
    assert 'inventory_operation_policy.OP_WAREHOUSE_EDIT' in doc
    assert 'translate(\'warehouse_name_label\')' in doc
    forbidden = ['from PyQt5.QtWidgets import QDialog', 'QSettings', 'database.', 'repositories.', 'requests']
    for token in forbidden:
        assert token not in doc, f'Forbidden token in warehouse document tab: {token}'

    init = read('alrajhi_client/features/inventory/__init__.py')
    assert 'WarehouseDocumentTab' in init

    main_window = read('alrajhi_client/views/main_window.py')
    assert 'def open_warehouse_document' in main_window
    assert 'WarehouseDocumentTab' in main_window

    widget = read('alrajhi_client/views/widgets/warehouses_widget.py')
    assert "open_warehouse_document()" in widget
    assert "open_warehouse_document(wh_id)" in widget
    assert "layout.addRow(translate('warehouse_name_label'), name)" in widget
    assert "layout.addRow(translate('item_name_label'), name)" not in widget

    tr = read('alrajhi_client/i18n/translator.py')
    for key in ('warehouse_document_new', 'warehouse_name_label', 'warehouse_code_label', 'warehouse_location_label'):
        assert key in tr, f'Missing i18n key: {key}'
    print('phase201_warehouse_document_tab_guard passed')

if __name__ == '__main__':
    main()
