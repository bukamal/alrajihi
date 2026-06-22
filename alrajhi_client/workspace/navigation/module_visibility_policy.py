# -*- coding: utf-8 -*-
"""Settings-backed navigation visibility for optional modules.

Phase 282: settings toggles must remove disabled modules from the main menu,
quick open, shortcuts, and direct page switching.  The policy is deliberately
small and read-only so UI code does not duplicate settings keys.
"""
from __future__ import annotations

from typing import Iterable

from core.services.settings_service import settings_service
from workspace.registry import PAGE_MANIFESTS


# Phase 331: page-level module visibility now derives from the UI registry.
# Keep settings-section checks below because grouped settings tabs are not
# one-to-one with visible workspace pages.
PAGE_MODULE_KEYS = {pid: manifest.module_checks for pid, manifest in PAGE_MANIFESTS.items()}


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
