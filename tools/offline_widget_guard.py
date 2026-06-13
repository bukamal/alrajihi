#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard UI refresh/list paths against unhandled offline REST read failures."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    'alrajhi_client/views/widgets/base_widget.py': ['is_offline_read_error', 'offline_read_message', 'تعذر التحديث: الخادم غير متصل'],
    'alrajhi_client/views/widgets/invoices_widget.py': ['def _is_offline_read_error', 'def _notify_offline_read', 'فواتير الشراء'],
    'alrajhi_client/views/widgets/returns_widget.py': ['is_offline_read_error', 'مرتجعات المبيعات', 'مرتجعات المشتريات'],
    'alrajhi_client/views/widgets/vouchers_widget.py': ['is_offline_read_error', 'السندات'],
    'alrajhi_client/views/widgets/customers_widget.py': ['is_offline_read_error', 'العملاء'],
    'alrajhi_client/views/widgets/suppliers_widget.py': ['is_offline_read_error', 'الموردين'],
    'alrajhi_client/views/widgets/warehouses_widget.py': ['is_offline_read_error', 'أرصدة المستودعات', 'تحويلات المستودعات'],
    'alrajhi_client/views/widgets/manufacturing_widget.py': ['is_offline_read_error', 'أوامر التصنيع'],
    'alrajhi_client/views/widgets/cashboxes_widget.py': ['is_offline_read_error', 'الصناديق والبنوك'],
    'alrajhi_client/views/dialogs/invoice_dialog.py': ['is_offline_read_error', 'الأطراف', 'المواد'],
    'alrajhi_client/views/dialogs/bom_dialog.py': ['is_offline_read_error', 'مواد التصنيع'],
    'alrajhi_client/views/dialogs/production_order_dialog.py': ['is_offline_read_error', 'مستودعات التصنيع'],
}

def main() -> int:
    errors = []
    for rel, markers in REQUIRED.items():
        path = ROOT / rel
        if not path.exists():
            errors.append(f'missing file: {rel}')
            continue
        text = path.read_text(encoding='utf-8')
        for marker in markers:
            if marker not in text:
                errors.append(f'{rel}: missing marker {marker!r}')
    if errors:
        print('Offline widget guard failed:')
        for e in errors:
            print(' -', e)
        return 1
    print('Offline widget guard: PASS')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
