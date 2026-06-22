# -*- coding: utf-8 -*-
"""Standalone cafe workspace activation contract.

Phase 313 keeps the cafe as a first-class workspace in navigation/settings while
preserving the shared restaurant engine for orders, payment, inventory,
printing, currency, and reporting.  The contract is intentionally pure-Python
so release guards can verify the architectural boundary without importing Qt.
"""
from __future__ import annotations

from typing import Mapping

CAFE_PAGE_ID = "cafe"
CAFE_SETTINGS_KEY = "cafe/enabled"
CAFE_ENGINE_BACKING = "restaurant"
CAFE_ORDER_TYPE = "cafe_quick_order"
CAFE_EMBEDDED_RESTAURANT_ENTRY_ALLOWED = False

CAFE_PERMISSION_KEYS: tuple[str, ...] = (
    "cafe.view",
    "cafe.order",
    "cafe.payment",
    "cafe.print",
    "cafe.report",
)

CAFE_VISIBLE_NAVIGATION_SECTIONS: tuple[str, ...] = (
    "quick_order",
    "barista",
    "shift_report",
)

CAFE_HIDDEN_RESTAURANT_SECTIONS: tuple[str, ...] = (
    "table_map",
    "table_operations",
    "merge_tables",
    "transfer_table",
    "guest_count_required",
)

CAFE_FORBIDDEN_ENGINE_FILES: tuple[str, ...] = (
    "cafe_gateway.py",
    "cafe_repository.py",
    "cafe_payment_service.py",
    "cafe_printing_service.py",
)


def cafe_page_enabled_from_settings(settings: Mapping[str, object] | None) -> bool:
    """Return the standalone cafe module visibility from a settings mapping."""
    data = dict(settings or {})
    raw = data.get(CAFE_SETTINGS_KEY)
    if raw is None:
        cafe_group = data.get("cafe")
        if isinstance(cafe_group, Mapping):
            raw = cafe_group.get("enabled")
    if raw is None:
        return True
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def cafe_standalone_navigation_contract() -> dict[str, object]:
    """Describe how the cafe appears as a standalone UI while sharing engine code."""
    return {
        "page_id": CAFE_PAGE_ID,
        "settings_key": CAFE_SETTINGS_KEY,
        "engine_backing": CAFE_ENGINE_BACKING,
        "order_type": CAFE_ORDER_TYPE,
        "visible_sections": CAFE_VISIBLE_NAVIGATION_SECTIONS,
        "hidden_restaurant_sections": CAFE_HIDDEN_RESTAURANT_SECTIONS,
        "permissions": CAFE_PERMISSION_KEYS,
        "forbidden_engine_files": CAFE_FORBIDDEN_ENGINE_FILES,
        "embedded_restaurant_entry_allowed": CAFE_EMBEDDED_RESTAURANT_ENTRY_ALLOWED,
    }


def cafe_uses_shared_restaurant_engine() -> bool:
    """Guard-friendly predicate: cafe has its own workspace, not its own engine."""
    contract = cafe_standalone_navigation_contract()
    return (
        contract["page_id"] == "cafe"
        and contract["engine_backing"] == "restaurant"
        and contract["order_type"] == "cafe_quick_order"
        and "table_map" in contract["hidden_restaurant_sections"]
    )


def cafe_is_decoupled_from_restaurant_visible_shell() -> bool:
    """Cafe must be a top-level workspace, not an embedded restaurant mode."""
    contract = cafe_standalone_navigation_contract()
    return (
        contract["page_id"] == "cafe"
        and contract["embedded_restaurant_entry_allowed"] is False
        and "quick_order" in contract["visible_sections"]
        and "merge_tables" in contract["hidden_restaurant_sections"]
    )
