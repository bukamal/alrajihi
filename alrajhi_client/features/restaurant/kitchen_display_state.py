# -*- coding: utf-8 -*-
"""Kitchen display state helpers for the restaurant operation shell.

The KDS must be deterministic for both local and remote gateways: active
orders are shown before completed tickets, older sent/preparing tickets are
promoted, and overdue tickets receive explicit metadata rather than relying on
color-only UI state.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any, Iterable

ACTIVE_KITCHEN_STATUSES = ("sent", "preparing", "ready")
TERMINAL_KITCHEN_STATUSES = ("served", "cancelled")
ALL_KITCHEN_STATUSES = ACTIVE_KITCHEN_STATUSES + TERMINAL_KITCHEN_STATUSES
DEFAULT_OVERDUE_MINUTES = 15

_STATUS_RANK = {
    "preparing": 0,
    "sent": 1,
    "ready": 2,
    "served": 3,
    "cancelled": 4,
}


def normalize_ticket_status(status: Any) -> str:
    value = str(status or "sent").strip().lower()
    return value if value in ALL_KITCHEN_STATUSES else "sent"


def parse_iso_datetime(value: Any) -> _dt.datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return _dt.datetime.fromisoformat(text)
    except Exception:
        return None


def ticket_elapsed_minutes(ticket: dict[str, Any], now: _dt.datetime | None = None) -> int:
    now = now or _dt.datetime.now()
    started = parse_iso_datetime(ticket.get("sent_at") or ticket.get("created_at") or ticket.get("opened_at"))
    if not started:
        return 0
    return max(0, int((now - started).total_seconds() // 60))


def ticket_priority_value(ticket: dict[str, Any]) -> int:
    try:
        return int(ticket.get("priority") or 0)
    except Exception:
        return 0


def ticket_is_overdue(ticket: dict[str, Any], threshold_minutes: int = DEFAULT_OVERDUE_MINUTES, now: _dt.datetime | None = None) -> bool:
    status = normalize_ticket_status(ticket.get("status"))
    if status not in {"sent", "preparing"}:
        return False
    return ticket_elapsed_minutes(ticket, now=now) >= max(1, int(threshold_minutes or DEFAULT_OVERDUE_MINUTES))


def decorate_kitchen_ticket(ticket: dict[str, Any], threshold_minutes: int = DEFAULT_OVERDUE_MINUTES, now: _dt.datetime | None = None) -> dict[str, Any]:
    payload = dict(ticket or {})
    status = normalize_ticket_status(payload.get("status"))
    payload["status"] = status
    payload["elapsed_minutes"] = ticket_elapsed_minutes(payload, now=now)
    payload["priority"] = ticket_priority_value(payload)
    payload["is_overdue"] = ticket_is_overdue(payload, threshold_minutes=threshold_minutes, now=now)
    payload["display_bucket"] = "active" if status in ACTIVE_KITCHEN_STATUSES else "closed"
    return payload


def kitchen_ticket_sort_key(ticket: dict[str, Any]) -> tuple[int, int, int, str]:
    payload = decorate_kitchen_ticket(ticket)
    status = normalize_ticket_status(payload.get("status"))
    active_bucket = 0 if status in ACTIVE_KITCHEN_STATUSES else 1
    # Highest priority first, then oldest active tickets first.
    return (
        active_bucket,
        -int(payload.get("priority") or 0),
        _STATUS_RANK.get(status, 9),
        str(payload.get("sent_at") or ""),
    )


def sort_kitchen_tickets(tickets: Iterable[dict[str, Any]], threshold_minutes: int = DEFAULT_OVERDUE_MINUTES) -> list[dict[str, Any]]:
    now = _dt.datetime.now()
    decorated = [decorate_kitchen_ticket(dict(ticket), threshold_minutes=threshold_minutes, now=now) for ticket in tickets or []]
    return sorted(decorated, key=kitchen_ticket_sort_key)


def status_filter_matches(status_filter: str, status: Any) -> bool:
    wanted = str(status_filter or "active").strip().lower()
    normalized = normalize_ticket_status(status)
    if wanted in ("", "active", "open"):
        return normalized in ACTIVE_KITCHEN_STATUSES
    if wanted == "all":
        return True
    return normalized == wanted
