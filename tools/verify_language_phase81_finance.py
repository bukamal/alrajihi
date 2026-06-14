# -*- coding: utf-8 -*-
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'alrajhi_client'))
from i18n import set_language, translate as tr

REQUIRED = [
    'finance_cashbanks_title','cashboxes','bank_accounts','financial_movements',
    'vouchers_title','receipt','payment','expense','customers_title','suppliers_title',
    'select_customer','select_supplier','remaining_invoice_amount','bank_accounts'
]

def main():
    for lang in ('ar','de','en'):
        set_language(lang)
        missing=[k for k in REQUIRED if tr(k)==k]
        if missing:
            raise SystemExit(f'{lang} missing translations: {missing}')
    files = [
        ROOT/'alrajhi_client/views/widgets/cashboxes_widget.py',
        ROOT/'alrajhi_client/views/widgets/vouchers_widget.py',
        ROOT/'alrajhi_client/views/widgets/customers_widget.py',
        ROOT/'alrajhi_client/views/widgets/suppliers_widget.py',
    ]
    for p in files:
        text=p.read_text(encoding='utf-8')
        if 'from i18n import translate as tr' not in text:
            raise SystemExit(f'missing tr import in {p}')
    print('OK phase81 finance localization')

if __name__ == '__main__':
    main()
