# -*- coding: utf-8 -*-
"""Cafe shift report contract built on the restaurant engine.

Phase 310 keeps cafe reporting as a focused operational view rather than a
separate accounting subsystem.  The report filters restaurant sessions to
``cafe_quick_order`` and exposes the cafe-specific facts a manager needs:
orders, payments, barista blockers, drink/add-on popularity, recipe inventory
consumption, and reorder alerts.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

CAFE_SHIFT_REPORT_REQUIRED_SECTIONS: Sequence[str] = (
    "period",
    "summary",
    "payment_methods",
    "open_orders",
    "top_drinks",
    "top_modifiers",
    "inventory_consumption",
    "low_stock_alerts",
    "operational_controls",
)

CAFE_SHIFT_CLOSE_BLOCKER_KEYS: Sequence[str] = (
    "open_orders",
    "unpaid_open_orders",
    "active_barista_tickets",
    "queued_print_jobs",
)


def decimal_text(value: Any, places: str = "0.00") -> str:
    try:
        dec = Decimal(str(value if value not in (None, "") else "0"))
    except (InvalidOperation, TypeError, ValueError):
        dec = Decimal("0")
    return str(dec.quantize(Decimal(places)))


def required_cafe_shift_report_sections() -> tuple[str, ...]:
    return tuple(CAFE_SHIFT_REPORT_REQUIRED_SECTIONS)


def cafe_shift_close_blocker_keys() -> tuple[str, ...]:
    return tuple(CAFE_SHIFT_CLOSE_BLOCKER_KEYS)


def cafe_shift_report_blockers(report: Mapping[str, Any] | None) -> tuple[str, ...]:
    controls = (report or {}).get("operational_controls") or {}
    blockers = controls.get("blockers") or []
    return tuple(str(item) for item in blockers if str(item).strip())


def cafe_shift_report_can_close(report: Mapping[str, Any] | None) -> bool:
    controls = (report or {}).get("operational_controls") or {}
    return bool(controls.get("can_close_shift") is True and not cafe_shift_report_blockers(report))


def build_cafe_operational_controls(
    *,
    open_orders: int,
    unpaid_open_orders: int,
    active_barista_tickets: int,
    queued_print_jobs: int,
) -> dict[str, Any]:
    values = {
        "open_orders": int(open_orders or 0),
        "unpaid_open_orders": int(unpaid_open_orders or 0),
        "active_barista_tickets": int(active_barista_tickets or 0),
        "queued_print_jobs": int(queued_print_jobs or 0),
    }
    blockers = [key for key in CAFE_SHIFT_CLOSE_BLOCKER_KEYS if values.get(key, 0) > 0]
    return {
        **values,
        "blockers": blockers,
        "can_close_shift": not blockers,
    }
