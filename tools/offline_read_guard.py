#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static guard for fragile remote reads in offline-critical save paths.

The guard is intentionally conservative: it checks that known write workflows
use explicit fallback wrappers instead of raw remote-only reads that can crash
when the server disappears between opening a form and pressing Save.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "invoice reference fallback": ("alrajhi_client/core/services/invoice_service.py", "def next_reference", "prefix = 'SOFF'"),
    "invoice duplicate-reference fallback": ("alrajhi_client/core/services/invoice_service.py", "def reference_exists", "تعذر فحص تكرار مرجع الفاتورة"),
    "invoice stock precheck fallback": ("alrajhi_client/views/dialogs/invoice_dialog.py", "def _stock_available_for_item", "تعذر فحص رصيد المادة"),
    "warehouse default fallback": ("alrajhi_client/core/services/warehouse_service.py", "def default_warehouse_id", "تعذر جلب المستودع الافتراضي"),
    "pos queued cash movement skip": ("alrajhi_client/core/services/cashbox_service.py", "def record_pos_sale", "int(invoice_id or 0) < 0"),
    "currency cache fallback": ("alrajhi_client/currency.py", "def get_current_rate", "_cached_or_default_rate"),
}

def main() -> int:
    errors = []
    for name, (rel, anchor, marker) in CHECKS.items():
        text = (ROOT / rel).read_text(encoding='utf-8')
        if anchor not in text or marker not in text:
            errors.append(f"{name}: missing {marker!r} in {rel}")
    if errors:
        print("Offline read guard failed:")
        for e in errors:
            print(" -", e)
        return 1
    print("Offline read guard: PASS")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
