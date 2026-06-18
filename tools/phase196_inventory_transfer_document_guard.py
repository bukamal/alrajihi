# -*- coding: utf-8 -*-
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def require(path, needle, message):
    text = (ROOT / path).read_text(encoding='utf-8')
    if needle not in text:
        raise SystemExit(message)

require('alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py', 'InventoryTransferDocumentTab(BaseDocumentTab)', 'InventoryTransferDocumentTab must be a real BaseDocumentTab')
require('alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py', 'barcode_input_service.lookup_entry', 'Transfer document must use unified barcode_input_service')
require('alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py', 'warehouse_service.create_transfer', 'Transfer document must save through warehouse_service')
require('alrajhi_client/features/inventory/grids/inventory_transfer_lines_model.py', 'conversion_factor', 'Transfer model must preserve conversion_factor')
require('alrajhi_client/features/inventory/grids/inventory_transfer_lines_model.py', 'base_qty', 'Transfer model must preserve base_qty')
require('alrajhi_client/views/widgets/warehouses_widget.py', 'open_inventory_transfer_document', 'Warehouse workspace must open transfer document tab first')
require('alrajhi_client/views/main_window.py', 'def open_inventory_transfer_document', 'MainWindow must expose transfer document opener')
require('alrajhi_client/database/repositories/warehouse_repo.py', 'base_qty', 'Local warehouse transfers must store base_qty')
require('alrajhi_server/repositories/http_route_sql/warehouses.py', 'base_qty', 'Server warehouse transfers must store base_qty')
require('alrajhi_client/i18n/translator.py', 'inventory_transfer_document_new', 'Transfer document i18n keys missing')
print('phase196_inventory_transfer_document_guard passed')
