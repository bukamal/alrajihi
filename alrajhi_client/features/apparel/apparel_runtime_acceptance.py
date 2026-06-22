# -*- coding: utf-8 -*-
"""Runtime acceptance helpers for the apparel color/size workflow.

Phase 322 closes the first apparel track by describing the scenario that must
remain true in local, API/network and multi-user contexts.  The helpers are
pure functions so tests, release gates and future smoke tools can validate the
workflow without importing PyQt or touching the UI.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping, Sequence


APPAREL_ACCEPTANCE_STEPS = (
    "create_base_item",
    "bulk_create_color_size_variants",
    "purchase_variant_stock",
    "scan_variant_barcode_for_sale",
    "post_sale_and_reduce_variant_stock",
    "return_same_variant",
    "transfer_variant_between_warehouses",
    "adjust_or_count_variant_stock",
    "review_apparel_report",
)

APPAREL_ACCEPTANCE_GUARDS = (
    "variant_barcode_resolves_exact_color_size",
    "invoice_line_keeps_variant_identity",
    "warehouse_movement_keeps_variant_identity",
    "reversal_preserves_variant_identity",
    "warehouse_transfer_preserves_variant_identity",
    "apparel_report_groups_by_color_size",
    "no_visible_sku_term_in_i18n",
    "network_api_uses_same_variant_payload",
    "rtl_ltr_shell_is_not_bypassed",
    "unified_printing_contract_is_not_bypassed",
)


def apparel_acceptance_step_keys() -> tuple[str, ...]:
    return APPAREL_ACCEPTANCE_STEPS


def apparel_acceptance_required_guards() -> tuple[str, ...]:
    return APPAREL_ACCEPTANCE_GUARDS


def _text(value: Any) -> str:
    return str(value or "").strip()


def _int_or_none(value: Any) -> int | None:
    try:
        if value in (None, "", 0, "0"):
            return None
        return int(value)
    except Exception:
        return None


def _dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")


def variant_identity(record: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize variant identity from a lookup, line, movement or transfer."""
    row = dict(record or {})
    matched_variant = row.get("matched_variant") if isinstance(row.get("matched_variant"), Mapping) else {}
    variant_id = _int_or_none(
        row.get("variant_id")
        or row.get("matched_variant_id")
        or matched_variant.get("variant_id")
        or matched_variant.get("id")
    )
    color = _text(row.get("variant_color") or row.get("color") or matched_variant.get("color"))
    size = _text(row.get("variant_size") or row.get("size") or matched_variant.get("size"))
    code = _text(row.get("variant_sku") or row.get("sku") or matched_variant.get("sku"))
    barcode = _text(row.get("matched_barcode") or row.get("barcode") or matched_variant.get("barcode"))
    scope = _text(row.get("barcode_scope") or ("variant" if variant_id else ""))
    return {
        "variant_id": variant_id,
        "variant_color": color,
        "variant_size": size,
        "variant_sku": code,
        "barcode_scope": scope,
        "matched_barcode": barcode,
        "is_variant": bool(variant_id and scope == "variant"),
    }


def barcode_lookup_acceptance(lookup: Mapping[str, Any] | None, *, color: str, size: str) -> bool:
    ident = variant_identity(lookup)
    return (
        ident["is_variant"]
        and ident["variant_color"].casefold() == _text(color).casefold()
        and ident["variant_size"].casefold() == _text(size).casefold()
    )


def line_keeps_variant_identity(line: Mapping[str, Any] | None, expected: Mapping[str, Any] | None) -> bool:
    actual = variant_identity(line)
    target = variant_identity(expected)
    return bool(
        actual["variant_id"]
        and actual["variant_id"] == target["variant_id"]
        and actual["variant_color"] == target["variant_color"]
        and actual["variant_size"] == target["variant_size"]
    )


def movement_keeps_variant_identity(movement: Mapping[str, Any] | None, expected: Mapping[str, Any] | None) -> bool:
    return line_keeps_variant_identity(movement, expected)


def transfer_keeps_variant_identity(transfer: Mapping[str, Any] | None, expected: Mapping[str, Any] | None) -> bool:
    return line_keeps_variant_identity(transfer, expected)


def reversal_keeps_variant_identity(original: Mapping[str, Any] | None, reversal: Mapping[str, Any] | None) -> bool:
    original_ident = variant_identity(original)
    reversal_ident = variant_identity(reversal)
    if not original_ident["is_variant"] or not reversal_ident["is_variant"]:
        return False
    return (
        original_ident["variant_id"] == reversal_ident["variant_id"]
        and original_ident["variant_color"] == reversal_ident["variant_color"]
        and original_ident["variant_size"] == reversal_ident["variant_size"]
        and _dec(original.get("quantity") if original else 0) == -_dec(reversal.get("quantity") if reversal else 0)
    )


def stock_delta_acceptance(before: Any, delta: Any, after: Any) -> bool:
    return _dec(before) + _dec(delta) == _dec(after)


def apparel_report_acceptance(report: Mapping[str, Any] | None, *, expected_variant_id: int | None = None) -> bool:
    report = dict(report or {})
    required = ("summary", "variants", "low_stock", "by_item", "by_color", "by_size")
    if any(key not in report for key in required):
        return False
    if expected_variant_id is None:
        return True
    for row in report.get("variants") or []:
        if _int_or_none(row.get("variant_id") or row.get("id")) == int(expected_variant_id):
            ident = variant_identity(row)
            return bool(ident["variant_color"] or ident["variant_size"])
    return False


def scenario_snapshot(*, item_name: str, color: str, size: str, quantity: Any, warehouse_name: str | None = None) -> dict[str, Any]:
    """Small serializable state snapshot used by tests and diagnostics."""
    return {
        "item_name": _text(item_name),
        "variant_color": _text(color),
        "variant_size": _text(size),
        "quantity": str(_dec(quantity)),
        "warehouse_name": _text(warehouse_name),
        "identity_label": " / ".join(part for part in (_text(item_name), _text(color), _text(size)) if part),
    }
