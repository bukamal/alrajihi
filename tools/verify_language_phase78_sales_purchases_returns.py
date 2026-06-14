# -*- coding: utf-8 -*-
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / 'alrajhi_client/views/widgets/invoices_widget.py',
    ROOT / 'alrajhi_client/views/widgets/returns_widget.py',
    ROOT / 'alrajhi_client/views/dialogs/invoice_dialog.py',
]
REQUIRED_TRANSLATE_KEYS = [
    'sales_invoices_title', 'purchase_invoices_title', 'sales_return', 'purchase_return',
    'search_sales_invoices', 'search_purchase_invoices', 'search_returns',
    'return_summary_sale', 'return_summary_purchase', 'confirm_delete_invoice_message',
]

def main():
    for path in FILES:
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    translator = (ROOT / 'alrajhi_client/i18n/translator.py').read_text(encoding='utf-8')
    missing = [key for key in REQUIRED_TRANSLATE_KEYS if key not in translator]
    if missing:
        raise SystemExit('missing translation keys: ' + ', '.join(missing))
    for path in FILES:
        text = path.read_text(encoding='utf-8')
        if 'from i18n import translate' not in text:
            raise SystemExit(f'{path}: missing i18n translate import')
    print('OK: phase78 sales/purchases/returns localization guard passed')

if __name__ == '__main__':
    main()
