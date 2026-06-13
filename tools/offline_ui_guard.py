#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard known UI refresh/list paths against remote read crashes in client/offline mode."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    'global offline exception hook': ('alrajhi_client/main.py', 'install_offline_exception_hook(app)'),
    'offline read utility': ('alrajhi_client/offline_read.py', 'def is_offline_read_error'),
    'invoice list refresh guard': ('alrajhi_client/views/widgets/invoices_widget.py', "_notify_offline_read('فواتير الشراء')"),
    'sales returns refresh guard': ('alrajhi_client/views/widgets/returns_widget.py', "notify_offline_read(self, 'مرتجعات المبيعات')"),
    'purchase returns refresh guard': ('alrajhi_client/views/widgets/returns_widget.py', "notify_offline_read(self, 'مرتجعات المشتريات')"),
    'voucher list refresh guard': ('alrajhi_client/views/widgets/vouchers_widget.py', "notify_offline_read(self, 'السندات')"),
    'users refresh guard': ('alrajhi_client/views/widgets/users_widget.py', "notify_offline_read(self, 'المستخدمون')"),
    'audit log refresh guard': ('alrajhi_client/views/widgets/audit_log_widget.py', "notify_offline_read(self, 'سجل التدقيق')"),
}

def main():
    errors = []
    for name, (rel, marker) in CHECKS.items():
        text = (ROOT / rel).read_text(encoding='utf-8')
        if marker not in text:
            errors.append(f'{name}: missing {marker!r} in {rel}')
    if errors:
        print('Offline UI guard failed:')
        for e in errors:
            print(' -', e)
        return 1
    print('Offline UI guard: PASS')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
