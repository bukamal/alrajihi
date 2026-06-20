# -*- coding: utf-8 -*-
from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import request

from alrajhi_server.api.audit_utils import audit_log


def audit_api_event(
    action: str,
    entity_type: str,
    *,
    entity_id_arg: str | None = None,
    audit_scope: str = "",
    permission_key: str = "",
    event_category: str = "api",
    branch_id_arg: str | None = None,
):
    """Best-effort decorator for API operations that are not already audited.

    It intentionally logs after successful function execution and never blocks
    the business operation.  Existing route-level audit_log calls remain the
    authoritative detailed audit for create/update/delete flows.
    """
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            try:
                entity_id = kwargs.get(entity_id_arg) if entity_id_arg else None
                branch_id = kwargs.get(branch_id_arg) if branch_id_arg else None
                if branch_id is None and request is not None:
                    branch_id = (request.get_json(silent=True) or {}).get('branch_id') or request.args.get('branch_id')
                audit_log(
                    action,
                    entity_type,
                    entity_id=entity_id,
                    new_values={'path': request.path if request else '', 'method': request.method if request else ''},
                    details=f'API {action} {entity_type}',
                    source='API',
                    audit_scope=audit_scope,
                    permission_key=permission_key,
                    branch_id=branch_id,
                    event_category=event_category,
                )
            except Exception:
                pass
            return result
        return wrapper
    return decorator


def audit_print_export(action: str, entity_type: str, entity_id: Any = None, *, audit_scope: str = '', permission_key: str = '', branch_id: Any = None, details: str = '') -> None:
    try:
        audit_log(
            action.upper(),
            entity_type,
            entity_id=entity_id,
            details=details or f'{action} {entity_type}',
            source='API',
            audit_scope=audit_scope,
            permission_key=permission_key,
            branch_id=branch_id,
            event_category='print_export',
        )
    except Exception:
        pass
