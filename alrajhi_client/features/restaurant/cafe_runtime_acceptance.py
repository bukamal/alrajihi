# -*- coding: utf-8 -*-
"""Cafe runtime acceptance contract.

Phase 311 freezes cafe operation as a first-class workflow while keeping the
implementation on the restaurant engine.  The contract deliberately avoids Qt
imports so it can be used by CI, release gates, and local smoke checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

from .cafe_shift_report import cafe_shift_report_blockers, cafe_shift_report_can_close
from .cafe_size_modifier_policy import CAFE_ORDER_TYPE, cafe_line_notes, is_cafe_order
from .restaurant_payment_split_policy import remaining_amount
from .restaurant_runtime_acceptance import kitchen_send_is_idempotent
from .restaurant_unified_printing_contract import payload_uses_unified_restaurant_printing, restaurant_print_document


@dataclass(frozen=True)
class CafeAcceptanceStep:
    key: str
    title_key: str
    required_guard: str


CAFE_RUNTIME_ACCEPTANCE_FLOW: Sequence[CafeAcceptanceStep] = (
    CafeAcceptanceStep("open_quick_order", "restaurant.cafe_new_quick_order", "cafe_order_uses_hidden_engine_table"),
    CafeAcceptanceStep("customize_drink", "restaurant.cafe_customize_item", "size_and_modifiers_are_line_metadata"),
    CafeAcceptanceStep("send_to_barista", "restaurant.cafe_send_to_barista", "barista_send_is_idempotent"),
    CafeAcceptanceStep("barista_progress", "restaurant.cafe_preparation", "barista_status_drives_handoff_state"),
    CafeAcceptanceStep("record_payment", "restaurant.record_payment", "cafe_payment_uses_restaurant_payment_policy"),
    CafeAcceptanceStep("print_receipt", "restaurant.cafe_print_receipt", "cafe_print_uses_browser_html_bridge"),
    CafeAcceptanceStep("close_order", "restaurant.cafe_checkout", "cafe_checkout_requires_full_payment"),
    CafeAcceptanceStep("shift_report", "restaurant.cafe_shift_report", "cafe_shift_closes_only_when_clear"),
)

CAFE_VISIBLE_WORKSPACE_SECTIONS: Sequence[str] = (
    "quick_order",
    "sizes",
    "modifiers",
    "barista",
    "payment",
    "receipt",
    "shift_report",
)

CAFE_HIDDEN_RESTAURANT_SECTIONS: Sequence[str] = (
    "table_map",
    "table_merge",
    "table_transfer",
    "guest_count_required",
)


def _decimal(value: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def cafe_acceptance_step_keys() -> tuple[str, ...]:
    return tuple(step.key for step in CAFE_RUNTIME_ACCEPTANCE_FLOW)


def cafe_acceptance_required_guards() -> tuple[str, ...]:
    return tuple(step.required_guard for step in CAFE_RUNTIME_ACCEPTANCE_FLOW)


def cafe_visible_workspace_sections() -> tuple[str, ...]:
    return tuple(CAFE_VISIBLE_WORKSPACE_SECTIONS)


def cafe_hidden_restaurant_sections() -> tuple[str, ...]:
    return tuple(CAFE_HIDDEN_RESTAURANT_SECTIONS)


def cafe_quick_order_visibility(session: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return the UI visibility contract for a cafe order.

    The local/server engine may retain a hidden Cafe table for referential
    integrity, but the user-facing cafe workflow must not expose table map or
    guest-management controls.
    """
    data = dict(session or {})
    order_type = str(data.get("order_type") or "").strip().lower()
    table_name = str(data.get("table_name") or data.get("table") or "").strip().lower()
    hidden_flag = bool(data.get("hidden_table") or data.get("is_hidden_table") or table_name == "cafe")
    cafe_order = order_type == CAFE_ORDER_TYPE or is_cafe_order(data)
    return {
        "order_type": order_type or CAFE_ORDER_TYPE,
        "is_cafe_order": cafe_order,
        "uses_hidden_engine_table": bool(cafe_order and hidden_flag),
        "show_table_map": False if cafe_order else True,
        "requires_guest_count": False if cafe_order else True,
    }


def cafe_barista_send_is_idempotent(first_result: Mapping[str, Any] | None, repeat_result: Mapping[str, Any] | None) -> bool:
    return kitchen_send_is_idempotent(first_result, repeat_result)


def cafe_payment_snapshot(total: Any, paid: Any) -> dict[str, Any]:
    total_dec = _decimal(total)
    paid_dec = _decimal(paid)
    remaining_dec = remaining_amount(total_dec, paid_dec)
    return {
        "total": str(total_dec),
        "paid": str(paid_dec),
        "remaining": str(remaining_dec),
        "is_fully_paid": total_dec > Decimal("0") and remaining_dec <= Decimal("0"),
        "can_checkout": total_dec > Decimal("0") and remaining_dec <= Decimal("0"),
    }


def cafe_checkout_allowed(total: Any, paid: Any, *, has_active_barista_tickets: bool = False) -> bool:
    balance = cafe_payment_snapshot(total, paid)
    return bool(balance["can_checkout"] and not has_active_barista_tickets)


def cafe_preparation_note(base_notes: str = "", size: Mapping[str, Any] | None = None, modifiers: list[dict[str, Any]] | None = None) -> str:
    return cafe_line_notes(base_notes=base_notes, size=dict(size or {}), modifiers=modifiers or [])


def cafe_print_payload_is_unified(payload: Mapping[str, Any] | None, kind: Any = "cafe_receipt") -> bool:
    return payload_uses_unified_restaurant_printing(payload, restaurant_print_document(kind).route_key)


def cafe_shift_acceptance(report: Mapping[str, Any] | None) -> dict[str, Any]:
    blockers = cafe_shift_report_blockers(report)
    return {
        "can_close_shift": cafe_shift_report_can_close(report),
        "blockers": blockers,
        "is_clear": not blockers,
    }
