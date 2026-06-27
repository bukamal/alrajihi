# -*- coding: utf-8 -*-
"""Phase 394 restaurant simple POS contract."""
from __future__ import annotations

RESTAURANT_SIMPLE_POS_CONTRACT = {
    "workspace": "restaurant",
    "factory": "RestaurantSimplePOSWidget",
    "exposed_sections": ("categories", "items", "invoice"),
    "removed_default_surfaces": ("kitchen_mode", "tables_mode", "analytics_mode", "kds"),
    "invoice_columns": ("item_name", "quantity", "unit_price", "total", "notes"),
    "checkout": "checkout_simple_pos_session",
}


def restaurant_simple_pos_contract() -> dict:
    return dict(RESTAURANT_SIMPLE_POS_CONTRACT)
