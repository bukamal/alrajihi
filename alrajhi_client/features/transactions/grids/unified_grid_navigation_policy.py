# -*- coding: utf-8 -*-
from __future__ import annotations

"""Qt-free runtime contract for transaction-grid navigation and row lifecycle.

This module is intentionally free of PyQt imports so the sales-invoice entry
contract can be tested in CI even on machines where the GUI runtime is not
installed.  The Qt table view delegates to this policy for the same invariants:

* Enter follows semantic business keys, not physical column numbers.
* Hidden columns are skipped by filtering the route through visible keys.
* Only one reusable trailing empty line is allowed.
* A row with an item/material/barcode identity is never treated as blank.
"""

from collections.abc import Callable, Iterable, MutableSequence
from copy import deepcopy
from typing import Any

SALES_INVOICE_ROUTE: tuple[str, ...] = (
    "item",
    "unit",
    "qty",
    "price",
    "discount",
    "tax",
    "total",
    "notes",
)

PURCHASE_INVOICE_ROUTE: tuple[str, ...] = (
    "item",
    "unit",
    "qty",
    "cost",
    "discount",
    "tax",
    "total",
    "notes",
)

SALES_RETURN_ROUTE: tuple[str, ...] = (
    "item",
    "unit",
    "qty",
    "reason",
    "restock",
    "price",
    "total",
    "notes",
)

PURCHASE_RETURN_ROUTE: tuple[str, ...] = (
    "item",
    "unit",
    "qty",
    "reason",
    "price",
    "total",
    "notes",
)

DOCUMENT_ENTER_ROUTES: dict[str, tuple[str, ...]] = {
    "sales_invoice": SALES_INVOICE_ROUTE,
    "purchase_invoice": PURCHASE_INVOICE_ROUTE,
    "sales_return": SALES_RETURN_ROUTE,
    "purchase_return": PURCHASE_RETURN_ROUTE,
}

KEY_ALIASES: dict[str, tuple[str, ...]] = {
    "item": ("item", "material", "product", "barcode"),
    "unit": ("unit", "uom", "unit_name"),
    "qty": ("qty", "quantity", "return_qty", "required_qty"),
    "price": ("price", "unit_price", "unit_value"),
    "cost": ("cost", "unit_cost", "price"),
    "discount": ("discount", "discount_amount"),
    "tax": ("tax", "tax_amount"),
    "total": ("total", "line_total", "total_cost"),
    "notes": ("notes", "description", "memo"),
    "reason": ("reason", "return_reason"),
    "restock": ("restock", "return_to_stock"),
}

IDENTITY_KEYS: tuple[str, ...] = (
    "item_id",
    "material_id",
    "product_id",
    "variant_id",
    "original_invoice_line_id",
)

TEXT_IDENTITY_KEYS: tuple[str, ...] = (
    "item",
    "material",
    "product",
    "barcode",
    "matched_barcode",
    "name",
    "item_name",
    "sku",
    "code",
)

DEFAULT_NUMERIC_ZERO_KEYS: tuple[str, ...] = (
    "qty",
    "quantity",
    "price",
    "cost",
    "discount",
    "tax",
    "total",
)


def normalize_key(key: str | None) -> str:
    return str(key or "").strip().casefold()


def aliases_for(route_key: str) -> tuple[str, ...]:
    key = normalize_key(route_key)
    return KEY_ALIASES.get(key, (key,))


def canonical_key_for(model_key: str | None) -> str:
    key = normalize_key(model_key)
    for canonical, aliases in KEY_ALIASES.items():
        if key == canonical or key in {normalize_key(alias) for alias in aliases}:
            return canonical
    return key


def semantic_route_for(document_type: str | None) -> tuple[str, ...]:
    return DOCUMENT_ENTER_ROUTES.get(str(document_type or "sales_invoice"), SALES_INVOICE_ROUTE)


def visible_semantic_route(document_type: str | None, visible_keys: Iterable[str]) -> tuple[str, ...]:
    """Return route keys that exist in the visible table keys.

    The result is semantic, not visual.  It preserves the official business
    route while skipping hidden or unavailable columns.  Barcode is considered
    an alias for item entry, but the stop remains the material/item slot.
    """
    visible = {normalize_key(key) for key in visible_keys or ()}
    resolved: list[str] = []
    for route_key in semantic_route_for(document_type):
        aliases = {normalize_key(alias) for alias in aliases_for(route_key)}
        if visible & aliases:
            resolved.append(route_key)
    return tuple(resolved)


def route_index_for_key(document_type: str | None, current_key: str, visible_keys: Iterable[str], *, forward: bool = True) -> str | None:
    route = visible_semantic_route(document_type, visible_keys)
    if not route:
        return None
    current = canonical_key_for(current_key)
    if current not in route:
        if current == "barcode" and "item" in route:
            current = "item"
        else:
            return None
    pos = route.index(current)
    if forward:
        return route[pos + 1] if pos + 1 < len(route) else None
    return route[pos - 1] if pos > 0 else None


def value_is_empty(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    if text in {"", "0", "0.0", "0.00", "0.000"}:
        return True
    if value in (0, 0.0):
        return True
    return False


def is_empty_transaction_line(row: dict[str, Any] | None) -> bool:
    if not isinstance(row, dict):
        return False
    for key in IDENTITY_KEYS:
        if row.get(key) not in (None, ""):
            return False
    for key in TEXT_IDENTITY_KEYS:
        if str(row.get(key) or "").strip():
            return False
    for key in DEFAULT_NUMERIC_ZERO_KEYS:
        if key in row and not value_is_empty(row.get(key)):
            # Non-zero money/quantity in an otherwise unidentified row is user data.
            return False
    return True


def trailing_empty_line_count(lines: Iterable[dict[str, Any]]) -> int:
    count = 0
    for row in reversed(list(lines or [])):
        if is_empty_transaction_line(row):
            count += 1
        else:
            break
    return count


def trim_extra_trailing_empty_lines(lines: MutableSequence[dict[str, Any]]) -> int:
    """Remove duplicate blank rows at the tail and return removals."""
    removed = 0
    while len(lines) > 1 and is_empty_transaction_line(lines[-1]) and is_empty_transaction_line(lines[-2]):
        lines.pop()
        removed += 1
    return removed


def ensure_single_trailing_empty_line(lines: MutableSequence[dict[str, Any]], factory: Callable[[], dict[str, Any]]) -> int:
    """Ensure and return the index of the reusable trailing blank row."""
    trim_extra_trailing_empty_lines(lines)
    if lines and is_empty_transaction_line(lines[-1]):
        return len(lines) - 1
    lines.append(factory())
    trim_extra_trailing_empty_lines(lines)
    return len(lines) - 1


def normalized_line_snapshot(lines: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Small immutable-ish snapshot used by diagnostics/tests."""
    return tuple(deepcopy(row) for row in lines or [])
