# -*- coding: utf-8 -*-
"""Restaurant shift report and close-control contract.

Phase 306 freezes the operational report that a restaurant manager needs before
ending a cashier/waiter shift.  It is intentionally pure and import-light so it
can be tested by CI, reused by local/remote gateways, and displayed by the
analytics panel without pulling in PyQt.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

SHIFT_REPORT_REQUIRED_SECTIONS: Sequence[str] = (
    "period",
    "summary",
    "payment_methods",
    "open_sessions",
    "top_items",
    "operational_controls",
)

SHIFT_CLOSE_BLOCKER_KEYS: Sequence[str] = (
    "open_sessions",
    "unpaid_open_sessions",
    "active_kitchen_tickets",
    "queued_print_jobs",
)


def decimal_text(value: Any, places: str = "0.00") -> str:
    try:
        dec = Decimal(str(value if value not in (None, "") else "0"))
    except (InvalidOperation, TypeError, ValueError):
        dec = Decimal("0")
    return str(dec.quantize(Decimal(places)))


def required_shift_report_sections() -> tuple[str, ...]:
    return tuple(SHIFT_REPORT_REQUIRED_SECTIONS)


def shift_close_blocker_keys() -> tuple[str, ...]:
    return tuple(SHIFT_CLOSE_BLOCKER_KEYS)


def shift_report_blockers(report: Mapping[str, Any] | None) -> tuple[str, ...]:
    controls = (report or {}).get("operational_controls") or {}
    blockers = controls.get("blockers") or []
    return tuple(str(item) for item in blockers if str(item).strip())


def shift_report_can_close(report: Mapping[str, Any] | None) -> bool:
    controls = (report or {}).get("operational_controls") or {}
    return bool(controls.get("can_close_shift") is True and not shift_report_blockers(report))


def build_operational_controls(
    *,
    open_sessions: int,
    unpaid_open_sessions: int,
    active_kitchen_tickets: int,
    queued_print_jobs: int,
) -> dict[str, Any]:
    values = {
        "open_sessions": int(open_sessions or 0),
        "unpaid_open_sessions": int(unpaid_open_sessions or 0),
        "active_kitchen_tickets": int(active_kitchen_tickets or 0),
        "queued_print_jobs": int(queued_print_jobs or 0),
    }
    blockers = [key for key in SHIFT_CLOSE_BLOCKER_KEYS if values.get(key, 0) > 0]
    return {
        **values,
        "blockers": blockers,
        "can_close_shift": not blockers,
    }
