# -*- coding: utf-8 -*-
"""Settings-backed navigation visibility for optional modules.

Phase 282: settings toggles must remove disabled modules from the main menu,
quick open, shortcuts, and direct page switching.  The policy is deliberately
small and read-only so UI code does not duplicate settings keys.
"""
from __future__ import annotations

from typing import Iterable

from core.services.settings_service import settings_service


PAGE_MODULE_KEYS = {
    'dashboard': (),
    'settings': (),
    'monitoring': (),
    'offline_queue': (),
    'sales_invoices': (('transactions/enabled', True),),
    'purchase_invoices': (('transactions/enabled', True),),
    'returns': (('transactions/enabled', True),),
    'purchase_returns': (('transactions/enabled', True),),
    'pos': (('pos/enabled', True),),
    'restaurant': (('restaurant/enabled', True),),
    'cafe': (('cafe/enabled', True),),
    'apparel': (('apparel/enabled', True),),
    'manufacturing': (('manufacturing/enabled', True),),
    'reports': (('reports/enabled', True),),
    'items': (('inventory/enabled', True),),
    'warehouses': (('inventory/enabled', True),),
    'categories': (('categories/enabled', True),),
    'cashboxes': (('finance/enabled', True),),
    'vouchers': (('finance/enabled', True),),
    'customers': (('parties/enabled', True),),
    'suppliers': (('parties/enabled', True),),
    'branches': (('branches/enabled', True),),
    'users': (('users/enabled', True),),
    'audit_log': (('users/enabled', True),),
}

SETTINGS_SECTION_KEYS = {
    'transactions': (('transactions/enabled', True),),
    'materials': (('inventory/enabled', True),),
    'inventory': (('inventory/enabled', True),),
    'categories': (('categories/enabled', True),),
    'finance': (('finance/enabled', True),),
    'parties': (('parties/enabled', True),),
    'branches': (('branches/enabled', True),),
    'manufacturing': (('manufacturing/enabled', True),),
    'reports': (('reports/enabled', True),),
    'pos': (('pos/enabled', True),),
    'restaurant': (('restaurant/enabled', True),),
    'cafe': (('cafe/enabled', True),),
    'apparel': (('apparel/enabled', True),),
    'users': (('users/enabled', True),),
}


def _enabled(checks: Iterable[tuple[str, bool]]) -> bool:
    for key, default in checks:
        try:
            if not settings_service.get_bool(key, default):
                return False
        except Exception:
            if default is False:
                return False
    return True


def page_enabled(page_id: str) -> bool:
    return _enabled(PAGE_MODULE_KEYS.get(page_id, ()))


def settings_section_enabled(section_id: str) -> bool:
    return _enabled(SETTINGS_SECTION_KEYS.get(section_id, ()))


def enabled_favorite_pages(pages: Iterable[str]) -> list[str]:
    return [pid for pid in pages if page_enabled(pid)]
