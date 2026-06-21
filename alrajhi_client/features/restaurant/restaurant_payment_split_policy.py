# -*- coding: utf-8 -*-
"""Restaurant payment and split-bill safety policy.

Phase 289 keeps restaurant payment behavior deterministic across local and
remote/server gateways.  The policy is intentionally pure-Python so both the
client gateway and the server repository can apply the same rules without UI
state leaks.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

TERMINAL_LINE_STATUSES = {"cancelled"}
UNSENT_LINE_STATUSES = {"new"}
PAYMENT_METHODS = {"cash", "card", "bank", "split", "mixed"}
SPLIT_OPEN = "open"
SPLIT_PAID = "paid"


def decimal_value(value: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def normalize_payment_method(method: Any) -> str:
    value = str(method or "cash").strip().lower()
    return value if value in PAYMENT_METHODS else "cash"


def line_amount(line: dict[str, Any] | None) -> Decimal:
    line = line or {}
    total = line.get("line_total") or line.get("total") or line.get("amount")
    if total not in (None, ""):
        return decimal_value(total)
    return decimal_value(line.get("quantity"), "0") * decimal_value(line.get("unit_price"), "0")


def billable_lines(lines: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [line for line in (lines or []) if str(line.get("kitchen_status") or "new").lower() not in TERMINAL_LINE_STATUSES]


def has_unsent_lines(lines: Iterable[dict[str, Any]] | None) -> bool:
    return any(str(line.get("kitchen_status") or "new").lower() in UNSENT_LINE_STATUSES for line in billable_lines(lines))


def require_payment_ready(lines: Iterable[dict[str, Any]] | None) -> None:
    usable = billable_lines(lines)
    if not usable:
        raise ValueError("Cannot collect restaurant payment for an empty bill")
    if has_unsent_lines(usable):
        raise ValueError("Send new order lines to kitchen before collecting payment")


def remaining_amount(total: Any, paid: Any) -> Decimal:
    remaining = decimal_value(total) - decimal_value(paid)
    return remaining if remaining > Decimal("0") else Decimal("0")


def split_status(subtotal: Any, paid: Any) -> str:
    subtotal_dec = decimal_value(subtotal)
    paid_dec = decimal_value(paid)
    return SPLIT_PAID if subtotal_dec > Decimal("0") and paid_dec >= subtotal_dec else SPLIT_OPEN


def cap_payment(amount: Any, outstanding: Any) -> Decimal:
    amount_dec = decimal_value(amount)
    if amount_dec <= Decimal("0"):
        raise ValueError("Payment amount must be greater than zero")
    outstanding_dec = decimal_value(outstanding)
    if outstanding_dec <= Decimal("0"):
        raise ValueError("Restaurant bill is already fully paid")
    return amount_dec if amount_dec <= outstanding_dec else outstanding_dec


def split_bill_summary(subtotal: Any, paid: Any) -> dict[str, Any]:
    subtotal_dec = decimal_value(subtotal)
    paid_dec = decimal_value(paid)
    remaining_dec = remaining_amount(subtotal_dec, paid_dec)
    return {
        "subtotal": str(subtotal_dec),
        "paid_amount": str(paid_dec),
        "remaining_amount": str(remaining_dec),
        "status": split_status(subtotal_dec, paid_dec),
        "is_paid": subtotal_dec > Decimal("0") and remaining_dec <= Decimal("0"),
    }
