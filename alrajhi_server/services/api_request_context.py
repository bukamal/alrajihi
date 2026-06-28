# -*- coding: utf-8 -*-
"""Request-scope metadata helpers for remote API parity.

The values extracted here are deliberately non-authoritative.  Permission,
branch access and audit decisions must still use the authenticated user and the
server database policies.  These helpers only standardize how routes read client
metadata such as idempotency keys, branch headers and offline replay markers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

try:  # Flask is optional for static/CI imports.
    from flask import request as flask_request
except Exception:  # pragma: no cover
    flask_request = None


@dataclass(frozen=True)
class ApiRequestContext:
    idempotency_key: str = ""
    branch_id: int | None = None
    source_branch_id: int | None = None
    target_branch_id: int | None = None
    offline_replay: bool = False
    sync_scope: str = ""
    conflict_policy: str = ""


def _first(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _to_int(value: Any) -> int | None:
    if value in (None, "", 0, "0"):
        return None
    try:
        return int(value)
    except Exception:
        return None


def _header(headers: Mapping[str, Any], *names: str) -> str:
    lowered = {str(k).lower(): v for k, v in dict(headers or {}).items()}
    for name in names:
        value = lowered.get(str(name).lower())
        if value not in (None, ""):
            return str(value).strip()
    return ""


def build_api_request_context(headers: Mapping[str, Any] | None = None, payload: Mapping[str, Any] | None = None, args: Mapping[str, Any] | None = None) -> ApiRequestContext:
    payload = payload or {}
    args = args or {}
    headers = headers or {}
    idempotency_key = _header(headers, "Idempotency-Key", "X-Idempotency-Key") or str(_first(payload.get("idempotency_key"), payload.get("client_request_id"), payload.get("offline_id")) or "").strip()
    branch_id = _to_int(_first(_header(headers, "X-Alrajhi-Branch-Id"), payload.get("branch_id"), args.get("branch_id")))
    source_branch_id = _to_int(_first(_header(headers, "X-Alrajhi-Source-Branch-Id"), payload.get("source_branch_id"), args.get("source_branch_id")))
    target_branch_id = _to_int(_first(_header(headers, "X-Alrajhi-Target-Branch-Id"), payload.get("target_branch_id"), args.get("target_branch_id")))
    offline_replay = _header(headers, "X-Alrajhi-Offline-Replay").lower() in {"1", "true", "yes", "y"}
    sync_scope = _header(headers, "X-Alrajhi-Sync-Scope")
    conflict_policy = _header(headers, "X-Alrajhi-Conflict-Policy")
    return ApiRequestContext(
        idempotency_key=idempotency_key,
        branch_id=branch_id,
        source_branch_id=source_branch_id,
        target_branch_id=target_branch_id,
        offline_replay=offline_replay,
        sync_scope=sync_scope,
        conflict_policy=conflict_policy,
    )


def current_api_request_context(payload: Mapping[str, Any] | None = None) -> ApiRequestContext:
    if flask_request is None:
        return build_api_request_context(payload=payload)
    try:
        return build_api_request_context(headers=flask_request.headers, payload=payload, args=flask_request.args)
    except Exception:
        return build_api_request_context(payload=payload)


__all__ = ["ApiRequestContext", "build_api_request_context", "current_api_request_context"]
