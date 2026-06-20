# -*- coding: utf-8 -*-
from __future__ import annotations

from functools import wraps
from typing import Any, Iterable

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity

from alrajhi_server.database.connection import get_db
from alrajhi_server.services.branch_access_policy import BranchAccessError, branch_access_policy


def _to_int(value: Any) -> int | None:
    if value in (None, '', 0, '0'):
        return None
    try:
        return int(value)
    except Exception:
        return None


def branch_denied_response(exc: Exception):
    return jsonify({'error': str(exc), 'code': 'BRANCH_ACCESS_DENIED'}), 403


def effective_restaurant_branch_id(user_id: Any, requested_branch_id: Any = None) -> int | None:
    return branch_access_policy.effective_branch_id(user_id, requested_branch_id)


def require_restaurant_branch(user_id: Any, branch_id: Any, *, context: str = 'restaurant') -> int | None:
    return branch_access_policy.require(user_id, branch_id, context=context)


def _set_cached_json_branch(branch_id: int | None) -> None:
    """Best-effort Flask request JSON update used by creation routes.

    Existing route handlers call ``request.get_json()`` themselves.  The guard
    runs after ``jwt_required`` and before the handler, so we update Flask's
    cached JSON payload when possible.  Handlers that explicitly pass
    ``branch_id=data.get('branch_id')`` then get the scoped branch without
    duplicating branch logic in every endpoint.
    """
    if branch_id is None:
        return
    try:
        data = request.get_json(silent=True) or {}
        if isinstance(data, dict):
            data['branch_id'] = branch_id
            request._cached_json = (data, data)  # Flask internals: silent/non-silent cache
    except Exception:
        pass


def scope_creation_payload(user_id: Any, *, requested_branch_id: Any = None, context: str = 'restaurant') -> int | None:
    requested = requested_branch_id
    if requested is None:
        try:
            data = request.get_json(silent=True) or {}
            requested = data.get('branch_id') if isinstance(data, dict) else None
        except Exception:
            requested = None
    branch_id = effective_restaurant_branch_id(user_id, requested)
    require_restaurant_branch(user_id, branch_id, context=context)
    _set_cached_json_branch(branch_id)
    return branch_id


def row_branch_id(row: dict[str, Any] | None) -> int | None:
    if not row:
        return None
    for key in ('branch_id', 'table_branch_id', 'session_branch_id', 'cashbox_branch_id', 'warehouse_branch_id'):
        value = _to_int(row.get(key))
        if value is not None:
            return value
    return None


def filter_restaurant_records(user_id: Any, rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    if branch_access_policy.can_view_all_branches(user_id):
        return list(rows or [])
    allowed = set(branch_access_policy.allowed_branch_ids(user_id))
    if not allowed:
        # Backward-compatible mode for legacy single-user databases that have
        # not populated user_branch_access yet.
        return list(rows or [])
    filtered: list[dict[str, Any]] = []
    for row in rows or []:
        bid = row_branch_id(row)
        if bid is None or bid in allowed:
            filtered.append(row)
    return filtered


def _query_one(sql: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
    row = get_db().execute(sql, params).fetchone()
    return dict(row) if row else None


def session_branch(session_id: Any) -> int | None:
    sid = _to_int(session_id)
    if sid is None:
        return None
    row = _query_one(
        """
        SELECT COALESCE(s.branch_id, t.branch_id) AS branch_id
        FROM restaurant_sessions s
        LEFT JOIN restaurant_tables t ON t.id=s.table_id
        WHERE s.id=?
        """,
        (sid,),
    )
    return row_branch_id(row)


def table_branch(table_id: Any) -> int | None:
    tid = _to_int(table_id)
    if tid is None:
        return None
    row = _query_one("SELECT branch_id FROM restaurant_tables WHERE id=?", (tid,))
    return row_branch_id(row)


def line_branch(line_id: Any) -> int | None:
    lid = _to_int(line_id)
    if lid is None:
        return None
    row = _query_one(
        """
        SELECT COALESCE(s.branch_id, t.branch_id) AS branch_id
        FROM restaurant_order_lines l
        JOIN restaurant_sessions s ON s.id=l.session_id
        LEFT JOIN restaurant_tables t ON t.id=s.table_id
        WHERE l.id=?
        """,
        (lid,),
    )
    return row_branch_id(row)


def ticket_branch(ticket_id: Any) -> int | None:
    tid = _to_int(ticket_id)
    if tid is None:
        return None
    row = _query_one(
        """
        SELECT COALESCE(kt.branch_id, s.branch_id, t.branch_id) AS branch_id
        FROM kitchen_tickets kt
        LEFT JOIN restaurant_sessions s ON s.id=kt.session_id
        LEFT JOIN restaurant_tables t ON t.id=s.table_id
        WHERE kt.id=?
        """,
        (tid,),
    )
    return row_branch_id(row)


def reservation_branch(reservation_id: Any) -> int | None:
    rid = _to_int(reservation_id)
    if rid is None:
        return None
    row = _query_one(
        """
        SELECT COALESCE(r.branch_id, t.branch_id) AS branch_id
        FROM restaurant_reservations r
        LEFT JOIN restaurant_tables t ON t.id=r.table_id
        WHERE r.id=?
        """,
        (rid,),
    )
    return row_branch_id(row)


def split_bill_branch(split_bill_id: Any) -> int | None:
    bid = _to_int(split_bill_id)
    if bid is None:
        return None
    row = _query_one(
        """
        SELECT COALESCE(s.branch_id, t.branch_id) AS branch_id
        FROM restaurant_split_bills b
        LEFT JOIN restaurant_sessions s ON s.id=b.session_id
        LEFT JOIN restaurant_tables t ON t.id=s.table_id
        WHERE b.id=?
        """,
        (bid,),
    )
    return row_branch_id(row)


def print_job_branch(job_id: Any) -> int | None:
    jid = _to_int(job_id)
    if jid is None:
        return None
    row = _query_one(
        """
        SELECT COALESCE(kt.branch_id, s.branch_id, t.branch_id) AS branch_id
        FROM restaurant_print_jobs j
        LEFT JOIN kitchen_tickets kt ON kt.id=j.ticket_id
        LEFT JOIN restaurant_sessions s ON s.id=kt.session_id
        LEFT JOIN restaurant_tables t ON t.id=s.table_id
        WHERE j.id=?
        """,
        (jid,),
    )
    return row_branch_id(row)


def restaurant_branch_guard(*, create: bool = False, context: str = 'restaurant'):
    """Decorator for restaurant operational routes.

    It enforces branch access based on common route variables such as
    ``session_id``, ``table_id``, ``line_id``, ``ticket_id`` and operation JSON
    references such as ``source_session_id`` and ``target_table_id``.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            try:
                if create:
                    scope_creation_payload(user_id, context=context)

                checks: list[tuple[str, int | None]] = []
                if 'session_id' in kwargs:
                    checks.append(('restaurant_session', session_branch(kwargs.get('session_id'))))
                if 'target_session_id' in kwargs:
                    checks.append(('restaurant_target_session', session_branch(kwargs.get('target_session_id'))))
                if 'table_id' in kwargs:
                    checks.append(('restaurant_table', table_branch(kwargs.get('table_id'))))
                if 'line_id' in kwargs:
                    checks.append(('restaurant_line', line_branch(kwargs.get('line_id'))))
                if 'ticket_id' in kwargs:
                    checks.append(('restaurant_kitchen_ticket', ticket_branch(kwargs.get('ticket_id'))))
                if 'reservation_id' in kwargs:
                    checks.append(('restaurant_reservation', reservation_branch(kwargs.get('reservation_id'))))
                if 'split_bill_id' in kwargs:
                    checks.append(('restaurant_split_bill', split_bill_branch(kwargs.get('split_bill_id'))))
                if 'job_id' in kwargs:
                    checks.append(('restaurant_print_job', print_job_branch(kwargs.get('job_id'))))

                data = request.get_json(silent=True) or {}
                if isinstance(data, dict):
                    if data.get('source_session_id') not in (None, ''):
                        checks.append(('restaurant_source_session', session_branch(data.get('source_session_id'))))
                    if data.get('target_table_id') not in (None, ''):
                        checks.append(('restaurant_target_table', table_branch(data.get('target_table_id'))))
                    if data.get('branch_id') not in (None, ''):
                        checks.append(('restaurant_payload', _to_int(data.get('branch_id'))))

                for label, branch_id in checks:
                    require_restaurant_branch(user_id, branch_id, context=label)
            except BranchAccessError as exc:
                return branch_denied_response(exc)
            except Exception:
                # The business method will return a 404/400 for missing records.
                # Do not convert unrelated lookup failures into branch denials.
                pass
            return fn(*args, **kwargs)
        return wrapper
    return decorator


__all__ = [
    'branch_denied_response',
    'effective_restaurant_branch_id',
    'filter_restaurant_records',
    'require_restaurant_branch',
    'restaurant_branch_guard',
    'scope_creation_payload',
]
