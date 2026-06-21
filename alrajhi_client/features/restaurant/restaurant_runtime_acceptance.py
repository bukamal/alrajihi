# -*- coding: utf-8 -*-
"""Restaurant runtime acceptance contract.

Phase 304 is not a visual feature phase.  It freezes the restaurant's field
workflow as a deterministic acceptance profile that can be exercised by CI and
by future hotfixes before a build is considered restaurant-ready.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping, Sequence

from .restaurant_order_state import (
    ORDER_CLOSED,
    ORDER_EDITING,
    ORDER_KITCHEN,
    ORDER_PAID,
    ORDER_PAYMENT_DUE,
    ORDER_READY,
    TABLE_FREE,
    TABLE_KITCHEN,
    TABLE_OCCUPIED,
    TABLE_PAYMENT,
    TABLE_READY,
    derive_order_state,
    derive_table_state,
)
from .restaurant_payment_split_policy import remaining_amount


@dataclass(frozen=True)
class RestaurantAcceptanceStep:
    key: str
    title_key: str
    required_guard: str


RESTAURANT_RUNTIME_ACCEPTANCE_FLOW: Sequence[RestaurantAcceptanceStep] = (
    RestaurantAcceptanceStep("open_table", "restaurant.open_table", "table_has_single_open_session"),
    RestaurantAcceptanceStep("add_order_lines", "restaurant.add_item", "new_lines_are_editing_only"),
    RestaurantAcceptanceStep("send_to_kitchen", "restaurant.send_to_kitchen", "only_new_lines_create_kitchen_tickets"),
    RestaurantAcceptanceStep("kitchen_progress", "restaurant.kitchen_display", "ticket_status_drives_table_state"),
    RestaurantAcceptanceStep("record_payment", "restaurant.record_payment", "payment_requires_sent_or_served_lines"),
    RestaurantAcceptanceStep("checkout", "restaurant.close_and_invoice", "checkout_requires_fully_paid_bill"),
    RestaurantAcceptanceStep("print_receipt", "restaurant.print_receipt", "printing_uses_central_browser_html_bridge"),
    RestaurantAcceptanceStep("release_table", "restaurant.table_released", "closed_session_releases_table"),
)


def _decimal(value: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def acceptance_step_keys() -> tuple[str, ...]:
    return tuple(step.key for step in RESTAURANT_RUNTIME_ACCEPTANCE_FLOW)


def acceptance_required_guards() -> tuple[str, ...]:
    return tuple(step.required_guard for step in RESTAURANT_RUNTIME_ACCEPTANCE_FLOW)


def kitchen_send_is_idempotent(first_result: Mapping[str, Any] | None, repeat_result: Mapping[str, Any] | None) -> bool:
    """Return True when the second kitchen send does not create duplicate KOTs."""
    first_tickets = list((first_result or {}).get("tickets") or [])
    repeat_tickets = list((repeat_result or {}).get("tickets") or [])
    return bool(first_tickets) and not repeat_tickets and (repeat_result or {}).get("message") == "no_new_lines"


def payment_snapshot(total: Any, paid: Any) -> dict[str, Any]:
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


def runtime_state_snapshot(
    lines: Iterable[dict[str, Any]] | None,
    total: Any,
    paid: Any,
    session_status: Any = "open",
    base_table_status: Any = "free",
) -> dict[str, Any]:
    balance = payment_snapshot(total, paid)
    order_state = derive_order_state(lines, balance, session_status=session_status)
    table_state = derive_table_state(lines, balance, session_status=session_status, base_table_status=base_table_status)
    return {
        "order_state": order_state,
        "table_state": table_state,
        "balance": balance,
        "can_checkout": bool(balance["can_checkout"] and order_state in {ORDER_PAID, ORDER_CLOSED}),
    }


def accepted_runtime_state_names() -> dict[str, str]:
    """Expose the canonical state names used by the restaurant acceptance gate."""
    return {
        "editing": ORDER_EDITING,
        "kitchen": ORDER_KITCHEN,
        "ready": ORDER_READY,
        "payment_due": ORDER_PAYMENT_DUE,
        "paid": ORDER_PAID,
        "closed": ORDER_CLOSED,
        "table_free": TABLE_FREE,
        "table_occupied": TABLE_OCCUPIED,
        "table_kitchen": TABLE_KITCHEN,
        "table_ready": TABLE_READY,
        "table_payment": TABLE_PAYMENT,
    }
