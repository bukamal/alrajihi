# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
checks = []

main = (ROOT / 'alrajhi_client/views/main_window.py').read_text(encoding='utf-8')
checks += [
    ('main opens invoice document tabs', 'from features.invoices import InvoiceEditorTab' in main),
    ('main opens voucher document tabs', 'from features.vouchers import VoucherEditorTab' in main),
    ('main opens return document tabs', 'def open_return_document' in main and 'features.returns' in main),
]

invoices = (ROOT / 'alrajhi_client/views/widgets/invoices_widget.py').read_text(encoding='utf-8')
checks += [
    ('invoice list delegates create to workspace', 'main.open_quick_invoice(inv_type)' in invoices),
    ('invoice list delegates edit to workspace', 'main.open_quick_invoice(inv_type, invoice_id=inv_id)' in invoices),
    ('invoice widget no longer instantiates InvoiceDialog directly', 'InvoiceDialog(' not in invoices),
]

returns = (ROOT / 'alrajhi_client/views/widgets/returns_widget.py').read_text(encoding='utf-8')
checks += [
    ('sales/purchase returns delegate to workspace', "open_return_document('sale'" in returns and "open_return_document('purchase'" in returns),
]

vouchers = (ROOT / 'alrajhi_client/views/widgets/vouchers_widget.py').read_text(encoding='utf-8')
checks += [
    ('vouchers delegate to workspace', 'open_quick_voucher' in vouchers and 'VoucherDialog(self, voucher)' in vouchers),
]

for rel in [
    'alrajhi_client/features/dialog_documents/dialog_document_tab.py',
    'alrajhi_client/features/invoices/invoice_editor_tab.py',
    'alrajhi_client/features/returns/return_editor_tabs.py',
    'alrajhi_client/features/vouchers/voucher_editor_tab.py',
]:
    checks.append((f'{rel} exists', (ROOT / rel).exists()))

failed = [name for name, ok in checks if not ok]
if failed:
    print('Phase 47 document tabs guard failed:')
    for name in failed:
        print(f' - {name}')
    sys.exit(1)
print('Phase 47 document tabs guard passed.')
