# -*- coding: utf-8 -*-
"""Phase444 contract for lazy-loaded page runtime and Windows packaging.

The UI shell now lazy-loads operational pages after startup.  That improves
login-to-main-window time, but it also means PyInstaller must explicitly retain
those modules in the packaged executable.  This contract is intentionally
Qt-free: it parses source/manifests and does not import widget modules.
"""
from __future__ import annotations

PHASE = 444
CONTRACT_NAME = "lazy_page_runtime_packaging"

REQUIRED_COLLECT_SUBMODULES = {
    "alrajhi_client.views",
    "alrajhi_client.views.widgets",
    "alrajhi_client.views.dialogs",
    "alrajhi_client.views.restaurant",
    "alrajhi_client.views.cafe",
    "alrajhi_client.views.apparel",
}

CRITICAL_LAZY_PAGE_IDS = {
    "pos",
    "restaurant",
    "cafe",
    "apparel",
    "reports",
    "settings",
    "manufacturing",
    "items",
    "sales_invoices",
    "purchase_invoices",
    "returns",
    "purchase_returns",
}

ERROR_MESSAGE_MUST_DISTINGUISH_IMPORT_FROM_API = True
