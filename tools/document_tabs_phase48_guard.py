# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
checks = []

invoice_dialog = (ROOT / 'alrajhi_client/views/dialogs/invoice_dialog.py').read_text(encoding='utf-8')
invoice_components = (ROOT / 'alrajhi_client/views/dialogs/invoice_document_components.py').read_text(encoding='utf-8')
invoice_tab = (ROOT / 'alrajhi_client/features/invoices/invoice_editor_tab.py').read_text(encoding='utf-8')
item_tab = (ROOT / 'alrajhi_client/features/items/item_editor_tab.py').read_text(encoding='utf-8')
product_service = (ROOT / 'alrajhi_client/core/services/product_service.py').read_text(encoding='utf-8')

checks += [
    ('invoice document components file exists', (ROOT / 'alrajhi_client/views/dialogs/invoice_document_components.py').exists()),
    ('invoice header component exists', 'class InvoiceHeaderComponent' in invoice_components),
    ('invoice lines component exists', 'class InvoiceLinesComponent' in invoice_components),
    ('invoice pricing engine exists', 'class InvoicePricingEngine' in invoice_components),
    ('invoice payments component exists', 'class InvoicePaymentsComponent' in invoice_components),
    ('invoice actions component exists', 'class InvoiceActionsComponent' in invoice_components),
    ('InvoiceDialog installs document components', 'def _install_document_components' in invoice_dialog and 'self.header_component' in invoice_dialog),
    ('InvoiceDialog exposes normalized document payload', 'def invoice_document_payload' in invoice_dialog),
    ('InvoiceEditorTab remains workspace entry point', 'class InvoiceEditorTab' in invoice_tab and 'embedded=True' in invoice_tab),
    ('invoice lines remain unit-aware', 'COL_UNIT' in invoice_dialog and 'conversion_factor' in invoice_dialog and 'base_qty' in invoice_dialog),
    ('item editor has units table', 'self.units_table' in item_tab and 'def _collect_item_units' in item_tab),
    ('item editor persists units through service', 'product_service.replace_units' in item_tab),
    ('product service has unit replacement API', 'def replace_units' in product_service),
]

failed = [name for name, ok in checks if not ok]
if failed:
    print('Phase 48 invoice/unit document guard failed:')
    for name in failed:
        print(f' - {name}')
    sys.exit(1)
print('Phase 48 invoice/unit document guard passed.')
