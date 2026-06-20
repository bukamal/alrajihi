# -*- coding: utf-8 -*-
"""Offline replay conflict/idempotency safety helpers.

This module is intentionally free of PyQt, database, and network imports.  It is
used by the local offline queue manager, the replay adapter, and CI audit tests.
Queued writes are allowed only because Phase 265 declared an explicit offline
sync contract; this module defines how those queued writes are replayed safely.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from workspace.sync.offline_sync_contract import (
    CONFLICT_CLIENT_REPLAY,
    CONFLICT_IDEMPOTENT_CREATE,
    CONFLICT_MANUAL_REVIEW,
    CONFLICT_SERVER_WINS,
)

REPLAY_STATUS_RETRY = "retry"
REPLAY_STATUS_SENT = "sent"
REPLAY_STATUS_FAILED = "failed"
REPLAY_STATUS_CONFLICT = "conflict"

# Validation/auth/not-found errors are not fixed by retrying the same queued
# payload.  409 is separated so the queue can keep the record for manual review.
PERMANENT_REPLAY_STATUS_CODES = frozenset({400, 401, 403, 404, 422})
CONFLICT_REPLAY_STATUS_CODES = frozenset({409})
RETRYABLE_REPLAY_STATUS_CODES = frozenset({408, 423, 425, 429, 500, 502, 503, 504})

_REFERENCE_KEYS = (
    "idempotency_key",
    "client_request_id",
    "offline_id",
    "pos_ticket_no",
    "ticket_no",
    "invoice_number",
    "return_no",
    "voucher_no",
    "expense_no",
    "reference",
    "number",
)


@dataclass(frozen=True)
class ReplaySafetyDecision:
    status: str
    status_code: int | None = None
    retryable: bool = False
    terminal: bool = False
    reason: str = ""


def extract_api_status_code(error: Exception | str | None) -> int | None:
    """Extract the API status code from RestClient error messages.

    RestClient raises strings such as ``API error 409 at http://...``.  Keeping
    this parser here avoids fragile string checks spread across the queue code.
    """
    if error is None:
        return None
    text = str(error)
    match = re.search(r"API error\s+(\d{3})", text)
    if match:
        try:
            return int(match.group(1))
        except Exception:
            return None
    return None


def _first_reference(data: Any) -> str:
    if not isinstance(data, Mapping):
        return ""
    for key in _REFERENCE_KEYS:
        value = data.get(key)
        if value not in (None, ""):
            return str(value).strip()
    # Try common nested POS/invoice payload containers without making this helper
    # depend on any feature package.
    for nested_key in ("invoice", "document", "payload"):
        nested = data.get(nested_key)
        if isinstance(nested, Mapping):
            nested_value = _first_reference(nested)
            if nested_value:
                return nested_value
    return ""


def build_idempotency_key(
    *,
    surface_key: str = "",
    payload_hash: str = "",
    record_id: int | str | None = None,
    data: Any = None,
) -> str:
    """Build a stable replay idempotency key for a queued request.

    Preference order:
    1. explicit business/client reference in the payload;
    2. record id for update/delete operations;
    3. canonical payload hash.
    """
    scope = str(surface_key or "offline").strip() or "offline"
    reference = _first_reference(data)
    if reference:
        return f"{scope}:ref:{reference}"
    if record_id not in (None, ""):
        return f"{scope}:record:{record_id}"
    if payload_hash:
        return f"{scope}:hash:{payload_hash}"
    return scope


def replay_headers(request_row: Mapping[str, Any]) -> dict[str, str]:
    """Headers attached to offline replay requests.

    Servers that do not yet persist idempotency keys will ignore these headers,
    but they are valuable for logs, proxies, and future server-side duplicate
    protection.  The client also uses the same key for local duplicate collapse.
    """
    headers: dict[str, str] = {"X-Alrajhi-Offline-Replay": "1"}
    idempotency_key = str(request_row.get("idempotency_key") or "").strip()
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
        headers["X-Idempotency-Key"] = idempotency_key
    sync_scope = str(request_row.get("sync_scope") or "").strip()
    if sync_scope:
        headers["X-Alrajhi-Sync-Scope"] = sync_scope
    conflict_policy = str(request_row.get("conflict_policy") or "").strip()
    if conflict_policy:
        headers["X-Alrajhi-Conflict-Policy"] = conflict_policy
    branch_id = request_row.get("branch_id")
    if branch_id not in (None, ""):
        headers["X-Alrajhi-Branch-Id"] = str(branch_id)
    return headers


def classify_replay_error(error: Exception | str, conflict_policy: str = "") -> ReplaySafetyDecision:
    status_code = extract_api_status_code(error)
    policy = str(conflict_policy or "").strip()
    if status_code in CONFLICT_REPLAY_STATUS_CODES:
        if policy == CONFLICT_SERVER_WINS:
            return ReplaySafetyDecision(
                status=REPLAY_STATUS_FAILED,
                status_code=status_code,
                terminal=True,
                reason="server conflict; server-wins policy marks queued payload obsolete",
            )
        return ReplaySafetyDecision(
            status=REPLAY_STATUS_CONFLICT,
            status_code=status_code,
            terminal=True,
            reason="server conflict requires manual review before replay",
        )
    if status_code in PERMANENT_REPLAY_STATUS_CODES:
        return ReplaySafetyDecision(
            status=REPLAY_STATUS_FAILED,
            status_code=status_code,
            terminal=True,
            reason="permanent API validation/auth/not-found error during replay",
        )
    if status_code in RETRYABLE_REPLAY_STATUS_CODES or status_code is None:
        return ReplaySafetyDecision(
            status=REPLAY_STATUS_RETRY,
            status_code=status_code,
            retryable=True,
            reason="transport or retryable server error during replay",
        )
    # Unknown 4xx/5xx codes are safer as manual review than endless retry.
    if 400 <= int(status_code or 0) < 500:
        return ReplaySafetyDecision(
            status=REPLAY_STATUS_CONFLICT if policy in {CONFLICT_MANUAL_REVIEW, CONFLICT_CLIENT_REPLAY, CONFLICT_IDEMPOTENT_CREATE} else REPLAY_STATUS_FAILED,
            status_code=status_code,
            terminal=True,
            reason="unclassified client-side API error during replay",
        )
    return ReplaySafetyDecision(status=REPLAY_STATUS_RETRY, status_code=status_code, retryable=True, reason="unclassified retryable replay error")


__all__ = [
    "ReplaySafetyDecision",
    "REPLAY_STATUS_RETRY",
    "REPLAY_STATUS_SENT",
    "REPLAY_STATUS_FAILED",
    "REPLAY_STATUS_CONFLICT",
    "PERMANENT_REPLAY_STATUS_CODES",
    "CONFLICT_REPLAY_STATUS_CODES",
    "RETRYABLE_REPLAY_STATUS_CODES",
    "build_idempotency_key",
    "classify_replay_error",
    "extract_api_status_code",
    "replay_headers",
]
