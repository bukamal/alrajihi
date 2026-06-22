# -*- coding: utf-8 -*-
"""Unified multi-barcode candidate providers for profile-aware label UIs.

Phase 339 completes the Phase 338 profile foundation by giving items, apparel,
restaurant and cafe screens one small adapter that feeds the same batch label
Dialog/Browser-HTML printing path.  UI widgets should not build barcode payloads
with sector-specific print code; they ask this module for profile candidates and
then pass them to ``BatchPrintDialog``/``printing_service``.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Iterable, List


def _format_price(value: Any) -> str:
    if value in (None, "", "—"):
        return ""
    try:
        from currency import currency
        amount = currency.convert(Decimal(str(value or 0)), currency.storage_currency(), currency.get_display_currency())
        return currency.format_amount(amount)
    except Exception:
        return str(value)


def _text(row: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(row.get(key, "") or "").strip()
        if value and value != "—":
            return value
    return ""


def _menu_barcode(row: Dict[str, Any], prefix: str = "MENU") -> str:
    return _text(row, "barcode", "code") or f"{prefix}-{row.get('id') or row.get('item_id') or '0'}"


def item_label_candidates(limit: int = 1000) -> List[Dict[str, Any]]:
    from core.services.catalog_service import catalog_service

    rows = catalog_service.items(limit=limit) or []
    result: List[Dict[str, Any]] = []
    for row in rows:
        barcode = _text(row, "barcode", "code")
        if not barcode:
            continue
        result.append({
            "id": row.get("id"),
            "name": _text(row, "name", "item_name"),
            "barcode": barcode,
            "price": _format_price(row.get("selling_price") or row.get("price")),
            "copies": 1,
        })
    return result


def apparel_variant_label_candidates(limit: int = 5000) -> List[Dict[str, Any]]:
    from core.services.product_service import product_service

    rows: List[Dict[str, Any]] = []
    for item in product_service.items(limit=limit, offset=0) or []:
        try:
            variants = product_service.item_variants(int(item.get("id") or 0))
        except Exception:
            variants = []
        for variant in variants:
            barcode = _text(variant, "barcode", "variant_barcode", "matched_barcode")
            if not barcode:
                continue
            rows.append({
                "id": variant.get("id"),
                "item_id": item.get("id"),
                "name": _text(item, "name", "item_name"),
                "item_name": _text(item, "name", "item_name"),
                "variant_color": _text(variant, "color", "variant_color"),
                "variant_size": _text(variant, "size", "variant_size"),
                "variant_code": _text(variant, "sku", "variant_code", "code"),
                "variant_barcode": barcode,
                "barcode": barcode,
                "price": _format_price(variant.get("sale_price") or item.get("selling_price") or item.get("price")),
                "copies": 1,
            })
    return rows


def restaurant_menu_label_candidates(limit: int = 1000) -> List[Dict[str, Any]]:
    from core.services.restaurant_service import restaurant_service

    result: List[Dict[str, Any]] = []
    # The local gateway caps the limit internally, which is acceptable for the
    # operational menu.  Remote gateways keep the same service contract.
    for row in restaurant_service.list_menu_items(limit=limit) or []:
        result.append({
            "id": row.get("id"),
            "name": _text(row, "name", "item_name", "menu_item"),
            "menu_item": _text(row, "name", "item_name", "menu_item"),
            "section": _text(row, "category_name", "category", "section"),
            "barcode": _menu_barcode(row, "MENU"),
            "price": _format_price(row.get("selling_price") or row.get("price")),
            "copies": 1,
        })
    return result


def restaurant_table_label_candidates() -> List[Dict[str, Any]]:
    from core.services.restaurant_service import restaurant_service

    result: List[Dict[str, Any]] = []
    for row in restaurant_service.list_tables() or []:
        code = _text(row, "barcode", "table_code", "code") or f"TABLE-{row.get('id') or _text(row, 'name') or '0'}"
        result.append({
            "id": row.get("id"),
            "name": _text(row, "name", "table_name", "table_number") or code,
            "table_name": _text(row, "name", "table_name", "table_number") or code,
            "zone": _text(row, "zone", "area", "section"),
            "barcode": code,
            "qr_value": _text(row, "qr_value", "qr") or code,
            "copies": 1,
        })
    return result


def cafe_product_label_candidates(limit: int = 1000) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in restaurant_menu_label_candidates(limit=limit):
        rows.append({
            **row,
            "product_name": row.get("name") or row.get("menu_item"),
            "size": row.get("size") or row.get("cup_size") or "",
            "barcode": row.get("barcode") or f"CAFE-{row.get('id') or '0'}",
        })
    return rows


def cafe_modifier_label_candidates() -> List[Dict[str, Any]]:
    from core.services.restaurant_service import restaurant_service

    rows: List[Dict[str, Any]] = []
    try:
        groups = restaurant_service.list_modifier_groups(include_inactive=False) or []
    except Exception:
        groups = []
    for group in groups:
        group_name = _text(group, "name", "group", "modifier_group")
        for option in group.get("options") or []:
            option_id = option.get("id") or option.get("option_id")
            code = _text(option, "barcode", "code") or f"MOD-{option_id or len(rows) + 1}"
            rows.append({
                "id": option_id,
                "group_id": group.get("id"),
                "name": _text(option, "name", "modifier_name"),
                "modifier_name": _text(option, "name", "modifier_name"),
                "group": group_name,
                "modifier_group": group_name,
                "barcode": code,
                "price": _format_price(option.get("price_delta") or option.get("price") or 0),
                "copies": 1,
            })
    return rows


PROFILE_CANDIDATE_PROVIDERS = {
    "items.default": item_label_candidates,
    "apparel.variant_labels": apparel_variant_label_candidates,
    "restaurant.menu_items": restaurant_menu_label_candidates,
    "restaurant.table_labels": restaurant_table_label_candidates,
    "cafe.products": cafe_product_label_candidates,
    "cafe.modifier_labels": cafe_modifier_label_candidates,
}


def barcode_profile_candidates(profile_id: str = "items.default") -> List[Dict[str, Any]]:
    provider = PROFILE_CANDIDATE_PROVIDERS.get(profile_id) or PROFILE_CANDIDATE_PROVIDERS["items.default"]
    return list(provider() or [])


def normalize_dialog_rows(rows: Iterable[Dict[str, Any]], profile_id: str = "items.default") -> List[Dict[str, Any]]:
    from printing.barcode_profiles import normalize_barcode_items

    normalized = normalize_barcode_items(rows or [], profile_id)
    for row in normalized:
        row.setdefault("copies", 1)
        row.setdefault("price", _format_price(row.get("selling_price") or row.get("sale_price") or row.get("price")))
    return normalized
