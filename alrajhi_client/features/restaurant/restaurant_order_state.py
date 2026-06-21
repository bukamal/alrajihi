# -*- coding: utf-8 -*-
"""Restaurant order/table state derivation.

Phase 287: keep the restaurant workflow deterministic.  The UI table state
must be derived from the active session, kitchen line states, and payment
balance rather than from a manually toggled table flag only.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

LINE_NEW = "new"
LINE_SENT = "sent"
LINE_PREPARING = "preparing"
LINE_READY = "ready"
LINE_SERVED = "served"
LINE_CANCELLED = "cancelled"

ORDER_EMPTY = "empty"
ORDER_EDITING = "editing"
ORDER_KITCHEN = "kitchen"
ORDER_READY = "ready"
ORDER_PAYMENT_DUE = "payment_due"
ORDER_PAID = "paid"
ORDER_CLOSED = "closed"

TABLE_FREE = "free"
TABLE_OCCUPIED = "occupied"
TABLE_KITCHEN = "kitchen"
TABLE_READY = "ready"
TABLE_PAYMENT = "payment"
TABLE_RESERVED = "reserved"

VALID_LINE_STATUSES = {LINE_NEW, LINE_SENT, LINE_PREPARING, LINE_READY, LINE_SERVED, LINE_CANCELLED}


def decimal_value(value: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def normalize_line_status(status: Any) -> str:
    value = str(status or LINE_NEW).strip().lower()
    return value if value in VALID_LINE_STATUSES else LINE_NEW


def line_counts(lines: Iterable[dict[str, Any]] | None) -> dict[str, int]:
    counts = {status: 0 for status in VALID_LINE_STATUSES}
    for line in lines or []:
        counts[normalize_line_status(line.get("kitchen_status"))] += 1
    return counts


def billable_line_count(lines: Iterable[dict[str, Any]] | None) -> int:
    return sum(1 for line in lines or [] if normalize_line_status(line.get("kitchen_status")) != LINE_CANCELLED)


def kitchen_state_from_lines(lines: Iterable[dict[str, Any]] | None) -> str:
    counts = line_counts(lines)
    billable = sum(count for status, count in counts.items() if status != LINE_CANCELLED)
    if billable <= 0:
        return ORDER_EMPTY
    if counts[LINE_NEW] > 0:
        return ORDER_EDITING
    if counts[LINE_SENT] > 0 or counts[LINE_PREPARING] > 0:
        return ORDER_KITCHEN
    if counts[LINE_READY] > 0:
        return ORDER_READY
    if counts[LINE_SERVED] > 0:
        return LINE_SERVED
    return ORDER_EMPTY


def is_fully_paid(balance: dict[str, Any] | None) -> bool:
    balance = balance or {}
    total = decimal_value(balance.get("total"), "0")
    remaining = decimal_value(balance.get("remaining"), "0")
    paid = decimal_value(balance.get("paid"), "0")
    return total > Decimal("0") and paid >= total and remaining <= Decimal("0")


def derive_order_state(lines: Iterable[dict[str, Any]] | None, balance: dict[str, Any] | None = None, session_status: Any = "open") -> str:
    if str(session_status or "open").lower() == "closed":
        return ORDER_CLOSED
    state = kitchen_state_from_lines(lines)
    if state == ORDER_EMPTY:
        return ORDER_EMPTY
    if state == ORDER_EDITING:
        return ORDER_EDITING
    if state == ORDER_KITCHEN:
        return ORDER_KITCHEN
    if is_fully_paid(balance):
        return ORDER_PAID
    if state == LINE_SERVED:
        return ORDER_PAYMENT_DUE
    return ORDER_READY


def derive_table_state(lines: Iterable[dict[str, Any]] | None, balance: dict[str, Any] | None = None, session_status: Any = "open", base_table_status: Any = "free") -> str:
    base = str(base_table_status or TABLE_FREE).strip().lower()
    if str(session_status or "").lower() != "open":
        return TABLE_RESERVED if base == TABLE_RESERVED else TABLE_FREE
    order_state = derive_order_state(lines, balance, session_status=session_status)
    if order_state in {ORDER_EMPTY, ORDER_EDITING}:
        return TABLE_OCCUPIED
    if order_state == ORDER_KITCHEN:
        return TABLE_KITCHEN
    if order_state == ORDER_READY:
        return TABLE_READY
    if order_state in {ORDER_PAYMENT_DUE, ORDER_PAID}:
        return TABLE_PAYMENT
    return TABLE_OCCUPIED


def db_table_status_for(table_state: str, base_table_status: Any = "occupied") -> str:
    """Map rich UI states to the persisted legacy restaurant_tables.status.

    Older code and migrations only understand free/occupied/reserved/payment.
    Rich states are exposed in list payloads while the DB keeps a compatible
    status value.
    """
    if table_state == TABLE_FREE:
        return TABLE_FREE
    if table_state == TABLE_RESERVED:
        return TABLE_RESERVED
    if table_state == TABLE_PAYMENT:
        return TABLE_PAYMENT
    return TABLE_OCCUPIED
